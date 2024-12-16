import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from langdetect import detect
import os
import re


class MemoryManager:

    def __init__(self, memory_file: str = "bella_memory.json"):
        self.memory_file = memory_file
        self.memory_data = self._load_memory()
        self.memory_retention = timedelta(days=30)
        self.backup_dir = "memory_backups"
        self.last_backup = None
        self.backup_interval = timedelta(hours=1)
        
        # Create backup directory if it doesn't exist
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
        
        # Auto-backup on initialization
        self._create_backup()
        
        # Enhanced memory integrity check
        if not self.verify_memory_integrity():
            print("Attempting to repair memory structure...")
            self._repair_memory()
            self._create_backup()  # Create backup after repair

    def _repair_memory(self):
        """Advanced memory repair function"""
        default_memory = self._create_default_memory()
        repaired = False

        # Deep merge of existing and default memory structures
        for key in default_memory:
            if key not in self.memory_data:
                self.memory_data[key] = default_memory[key]
                repaired = True
            elif isinstance(default_memory[key], dict):
                for subkey in default_memory[key]:
                    if subkey not in self.memory_data[key]:
                        self.memory_data[key][subkey] = default_memory[key][subkey]
                        repaired = True

        # Validate data types
        for key in self.memory_data:
            if key in default_memory:
                if not isinstance(self.memory_data[key], type(default_memory[key])):
                    self.memory_data[key] = default_memory[key]
                    repaired = True

        if repaired:
            self._save_memory()
            print("Memory structure repaired successfully")

    def _create_backup(self):
        """Enhanced backup system with rotation and validation"""
        current_time = datetime.now()
        
        # Check if backup is needed based on interval
        if self.last_backup and (current_time - self.last_backup) < self.backup_interval:
            return

        timestamp = current_time.strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(self.backup_dir, f"bella_memory_backup_{timestamp}.json")
        
        try:
            # Create new backup
            with open(self.memory_file, 'r') as source:
                memory_data = json.load(source)
                with open(backup_path, 'w') as backup:
                    json.dump(memory_data, backup, indent=4)
            
            # Validate backup
            with open(backup_path, 'r') as backup:
                backup_data = json.load(backup)
                if backup_data != memory_data:
                    raise ValueError("Backup validation failed")
            
            # Update last backup time
            self.last_backup = current_time
            
            # Rotate backups (keep last 10 instead of 5)
            backups = sorted([f for f in os.listdir(self.backup_dir) if f.endswith('.json')])
            if len(backups) > 10:
                for old_backup in backups[:-10]:
                    os.remove(os.path.join(self.backup_dir, old_backup))
                    
        except Exception as e:
            print(f"Backup creation failed: {str(e)}")
            # Try to restore from last good backup if current backup fails
            self._restore_from_last_backup()

    def _restore_from_last_backup(self):
        """Restore memory from most recent valid backup"""
        try:
            backups = sorted([f for f in os.listdir(self.backup_dir) if f.endswith('.json')], reverse=True)
            
            for backup_file in backups:
                backup_path = os.path.join(self.backup_dir, backup_file)
                try:
                    with open(backup_path, 'r') as backup:
                        data = json.load(backup)
                        # Validate backup structure
                        if self._validate_memory_structure(data):
                            self.memory_data = data
                            self._save_memory()
                            print(f"Successfully restored from backup: {backup_file}")
                            return True
                except:
                    continue
                    
            print("No valid backups found")
            return False
            
        except Exception as e:
            print(f"Restore failed: {str(e)}")
            return False

    def _validate_memory_structure(self, data: Dict) -> bool:
        """Validate memory structure against required schema"""
        required_keys = {
            "users": dict,
            "conversations": dict,
            "instructions": dict,
            "behavior_notes": list,
            "owner_commands": dict,
            "punishment_rules": dict,
            "behavior_rules": dict,
            "emotional_states": list,
            "analytics": dict,
            "user_reputation": dict,
            "conversation_summaries": dict,
            "backups": list,
            "memorable_phrases": list,
            "message_patterns": dict,
            "conversation_styles": dict,
            "user_preferences": dict,
            "interaction_metrics": dict,
            "relationships": dict,
            "user_notes": dict,
            "media_interactions": dict
        }

        try:
            for key, expected_type in required_keys.items():
                if key not in data:
                    return False
                if not isinstance(data[key], expected_type):
                    return False
            return True
        except:
            return False

    def add_conversation(self, user_id: str, message: str, response: str, is_owner: bool = False):
        """Enhanced conversation tracking with analytics"""
        if "conversations" not in self.memory_data:
            self.memory_data["conversations"] = {}
            
        if user_id not in self.memory_data["conversations"]:
            self.memory_data["conversations"][user_id] = {}
            
        timestamp = datetime.now().isoformat()
        
        # Enhanced context tracking
        context = {
            "timestamp": timestamp,
            "message_type": "owner_message" if is_owner else "user_message",
            "sentiment": self._analyze_sentiment(message),
            "topics": self._extract_topics(message),
            "language": detect(message),
            "message_length": len(message),
            "response_length": len(response),
            "interaction_time": timestamp
        }
        
        # Store conversation with enhanced metadata
        self.memory_data["conversations"][user_id][timestamp] = {
            "message": message,
            "response": response,
            "is_owner": is_owner,
            "context": context
        }
        
        # Update analytics
        self._update_analytics(user_id, context)
        
        # Auto-backup on significant changes
        if len(self.memory_data["conversations"][user_id]) % 10 == 0:
            self._create_backup()
            
        self._save_memory()

    def _analyze_sentiment(self, text: str) -> str:
        """Basic sentiment analysis"""
        positive_words = {'love', 'great', 'awesome', 'amazing', 'good', 'thanks', 'please'}
        negative_words = {'hate', 'bad', 'stupid', 'dumb', 'idiot', 'fuck', 'shit'}
        
        text_words = set(text.lower().split())
        
        pos_count = len(text_words.intersection(positive_words))
        neg_count = len(text_words.intersection(negative_words))
        
        if pos_count > neg_count:
            return "very_positive" if pos_count > 2 else "positive"
        elif neg_count > pos_count:
            return "very_negative" if neg_count > 2 else "negative"
        return "neutral"

    def _extract_topics(self, text: str) -> List[str]:
        """Extract main topics from text"""
        # Add your topic extraction logic here
        # This is a simple example
        common_topics = {
            'greeting': ['hi', 'hello', 'hey'],
            'farewell': ['bye', 'goodbye', 'cya'],
            'help': ['help', 'assist', 'support'],
            'command': ['!', '/', 'command'],
            'emotion': ['feel', 'happy', 'sad', 'angry']
        }
        
        found_topics = []
        text_lower = text.lower()
        
        for topic, keywords in common_topics.items():
            if any(keyword in text_lower for keyword in keywords):
                found_topics.append(topic)
                
        return found_topics

    def _update_analytics(self, user_id: str, context: Dict):
        """Update analytics with new interaction data"""
        if "analytics" not in self.memory_data:
            self.memory_data["analytics"] = {
                "user_engagement": {},
                "command_usage": {},
                "response_metrics": {},
                "error_logs": [],
                "performance_metrics": {}
            }
            
        # Update user engagement
        if user_id not in self.memory_data["analytics"]["user_engagement"]:
            self.memory_data["analytics"]["user_engagement"][user_id] = {
                "total_messages": 0,
                "avg_message_length": 0,
                "sentiment_distribution": {
                    "positive": 0,
                    "negative": 0,
                    "neutral": 0
                },
                "active_hours": {},
                "topics_discussed": {}
            }
            
        engagement = self.memory_data["analytics"]["user_engagement"][user_id]
        engagement["total_messages"] += 1
        
        # Update average message length
        engagement["avg_message_length"] = (
            (engagement["avg_message_length"] * (engagement["total_messages"] - 1) +
             context["message_length"]) / engagement["total_messages"]
        )
        
        # Update sentiment distribution
        sentiment = context["sentiment"]
        if "positive" in sentiment:
            engagement["sentiment_distribution"]["positive"] += 1
        elif "negative" in sentiment:
            engagement["sentiment_distribution"]["negative"] += 1
        else:
            engagement["sentiment_distribution"]["neutral"] += 1
            
        # Update active hours
        hour = datetime.fromisoformat(context["timestamp"]).hour
        engagement["active_hours"][str(hour)] = engagement["active_hours"].get(str(hour), 0) + 1
        
        # Update topics
        for topic in context["topics"]:
            engagement["topics_discussed"][topic] = engagement["topics_discussed"].get(topic, 0) + 1

    def _load_memory(self) -> Dict:
        """Enhanced memory loading with corruption handling"""
        try:
            # Try to load the main memory file
            with open(self.memory_file, 'r') as f:
                data = json.load(f)
                
            # Initialize missing keys instead of replacing everything
            default_memory = self._create_default_memory()
            
            # Merge existing data with default structure
            for key in default_memory:
                if key not in data:
                    data[key] = default_memory[key]
            
            return data
                
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Memory load failed: {str(e)}, creating new memory file")
            return self._create_default_memory()

    def _create_default_memory(self) -> Dict:
        """Create default memory structure"""
        return {
            "users": {},
            "conversations": {},
            "instructions": {},
            "behavior_notes": [],
            "owner_commands": {
                "permanent": [],
                "temporary": []
            },
            "punishment_rules": {},
            "behavior_rules": {},
            "emotional_states": [],
            "analytics": {
                "user_engagement": {},
                "command_usage": {},
                "response_metrics": {},
                "error_logs": [],
                "performance_metrics": {}
            },
            "user_reputation": {},
            "conversation_summaries": {},
            "backups": [],
            "memorable_phrases": [],
            "message_patterns": {},
            "conversation_styles": {},
            "last_cleaned": datetime.now().isoformat(),
            "media_interactions": {
                "images": {},
                "voice_messages": {},
                "last_processed": None
            }
        }

    def _save_memory(self):
        """Enhanced save with error handling"""
        try:
            # Create backup of current file if it exists
            if os.path.exists(self.memory_file):
                backup_file = f"{self.memory_file}.bak"
                with open(self.memory_file, 'r') as source:
                    with open(backup_file, 'w') as backup:
                        backup.write(source.read())
            
            # Save new data
            with open(self.memory_file, 'w') as f:
                json.dump(self.memory_data, f, indent=4)
                
        except Exception as e:
            print(f"Memory save failed: {str(e)}")
            # If save failed and backup exists, restore from backup
            if os.path.exists(f"{self.memory_file}.bak"):
                os.replace(f"{self.memory_file}.bak", self.memory_file)

    def _recover_from_backup(self):
        """Recover memory from most recent backup"""
        try:
            backups = sorted([f for f in os.listdir(self.backup_dir) if f.endswith('.json')])
            if backups:
                latest_backup = os.path.join(self.backup_dir, backups[-1])
                with open(latest_backup, 'r') as f:
                    self.memory_data = json.load(f)
                print("Successfully recovered from backup")
            else:
                print("No backups available for recovery")
        except Exception as e:
            print(f"Recovery failed: {str(e)}")

    def _clean_old_memories(self):
        current_time = datetime.now()
        last_cleaned = self.memory_data.get("last_cleaned")

        if last_cleaned and (current_time -
                             datetime.fromisoformat(last_cleaned)).days < 1:
            return  # Only clean once per day

        for user_id in list(self.memory_data["conversations"].keys()):
            conversations = self.memory_data["conversations"][user_id]
            recent_convos = {}

            for timestamp, convo in conversations.items():
                if (current_time - datetime.fromisoformat(timestamp)
                    ) <= self.memory_retention:
                    recent_convos[timestamp] = convo

            if recent_convos:
                self.memory_data["conversations"][user_id] = recent_convos
            else:
                del self.memory_data["conversations"][user_id]

        self.memory_data["last_cleaned"] = current_time.isoformat()
        self._save_memory()

    def add_user_info(self, user_id: str, info: Dict):
        """Store or update user information"""
        if "users" not in self.memory_data:
            self.memory_data["users"] = {}
            
        if user_id not in self.memory_data["users"]:
            self.memory_data["users"][user_id] = {
                "name": None,
                "first_seen": datetime.now().isoformat(),
                "last_seen": datetime.now().isoformat(),
                "preferences": {},
                "traits": [],
                "personal_info": {},
                "nicknames": [],
                "remembered_facts": [],
                "conversation_style": "default"
            }
        
        user_data = self.memory_data["users"][user_id]
        user_data["last_seen"] = datetime.now().isoformat()
        
        # Update specific fields while preserving existing data
        if "name" in info:
            user_data["personal_info"]["name"] = info["name"]
            if info["name"] not in user_data["nicknames"]:
                user_data["nicknames"].append(info["name"])
                
        if "fact" in info:
            if info["fact"] not in user_data["remembered_facts"]:
                user_data["remembered_facts"].append({
                    "fact": info["fact"],
                    "timestamp": datetime.now().isoformat()
                })
                
        if "preference" in info:
            user_data["preferences"][info["preference"]["type"]] = info["preference"]["value"]
            
        self._save_memory()

    def add_conversation(self, user_id: str, message: str, response: str, is_owner: bool):
        """Enhanced conversation storage with detailed memory"""
        if "conversations" not in self.memory_data:
            self.memory_data["conversations"] = {}

        if user_id not in self.memory_data["conversations"]:
            self.memory_data["conversations"][user_id] = {}

        timestamp = datetime.now().isoformat()
        
        # Enhanced context tracking with more details
        context = {
            "timestamp": timestamp,
            "message_type": self._determine_message_type(message),
            "sentiment": self._analyze_sentiment(message),
            "language": detect(message) if message else "unknown",
            "user_state": self._get_user_state(user_id),
            "conversation_chain": self._get_conversation_chain(user_id),
            "active_rules": self._get_active_rules(user_id),
            "environmental_context": {
                "time_of_day": datetime.now().strftime("%H:%M"),
                "day_of_week": datetime.now().strftime("%A"),
                "server_load": self._get_server_load()
            },
            "keywords": self._extract_keywords(message),
            "topics": self._identify_topics(message),
            "references": self._find_references(message),
            "emotional_context": self._get_emotional_context()
        }
        
        self.memory_data["conversations"][user_id][timestamp] = {
            "message": message,
            "response": response,
            "is_owner": is_owner,
            "context": context,
            "related_memories": self._find_related_memories(message, user_id),
            "instruction_references": self._find_relevant_instructions(message)
        }

        # Process and store detailed patterns
        self._process_conversation_patterns(user_id, message, context)
        self._save_memory()

    def get_recent_conversations(self,
                                 user_id: str,
                                 limit: int = 5) -> List[Dict]:
        """Get recent conversations with a user"""
        if user_id not in self.memory_data.get("conversations", {}):
            return []

        conversations = self.memory_data["conversations"][user_id]
        sorted_convos = sorted([{
            "timestamp": ts,
            **conv
        } for ts, conv in conversations.items()],
                               key=lambda x: x["timestamp"],
                               reverse=True)

        return sorted_convos[:limit]

    def get_user_info(self, user_id: str) -> Dict:
        """Get comprehensive user information"""
        if user_id not in self.memory_data["users"]:
            self.memory_data["users"][user_id] = {
                "name": None,
                "first_seen": datetime.now().isoformat(),
                "last_seen": datetime.now().isoformat(),
                "preferences": {},
                "traits": [],
                "personal_info": {
                    "name": None,
                    "remembered_facts": [],
                    "nicknames": []
                },
                "conversation_style": "default",
                "sentiment_history": []
            }
        return self.memory_data["users"][user_id]

    def get_conversation_summary(self, user_id: str) -> str:
        """Enhanced conversation summary with better context"""
        recent_convos = self.get_recent_conversations(user_id, limit=10)  # Increased from 5
        user_info = self.get_user_info(user_id)
        behavior_rules = self.get_user_behavior_rules(user_id)
        punishment_history = self.get_punishment_history(user_id)

        if not any([recent_convos, user_info, behavior_rules, punishment_history]):
            return ""

        summary = []
        
        if user_info:
            summary.append("👤 User Profile:")
            for key, value in user_info.items():
                summary.append(f"- {key}: {value}")

        if behavior_rules:
            summary.append("\n🎭 Behavior Rules:")
            summary.append(behavior_rules)

        if punishment_history:
            summary.append("\n⚠️ Punishment History:")
            summary.append(punishment_history)

        if recent_convos:
            summary.append("\n💬 Recent Interactions:")
            for convo in recent_convos:
                timestamp = datetime.fromisoformat(convo["timestamp"]).strftime("%Y-%m-%d %H:%M")
                context = convo.get("context", {})
                summary.append(f"[{timestamp}] ({context.get('message_type', 'conversation')})")
                summary.append(f"User: {convo['message']}")
                summary.append(f"Bella: {convo['response']}")
                if context.get("sentiment"):
                    summary.append(f"Sentiment: {context['sentiment']}")
                summary.append("")

        return "\n".join(summary)

    def get_punishment_history(self, user_id: str) -> str:
        """Get user's punishment history"""
        if "punishment_rules" not in self.memory_data:
            return ""

        history = []
        for rule_id, rule in self.memory_data["punishment_rules"].items():
            if rule_id == user_id:
                timestamp = datetime.fromisoformat(rule["timestamp"]).strftime("%Y-%m-%d %H:%M")
                punishment_type = rule["type"]
                duration = f" for {rule['duration']} minutes" if rule.get("duration") else ""
                status = "Active" if rule.get("active", True) else "Inactive"
                history.append(f"[{timestamp}] {status} - {punishment_type}{duration}")

        return "\n".join(history) if history else ""

    def get_all_users_summary(self) -> str:
        """Get a summary of all users Bella has interacted with"""
        summary = []
        for user_id, conversations in self.memory_data.get(
                "conversations", {}).items():
            # Get the most recent conversation
            sorted_convos = sorted(conversations.items(),
                                   key=lambda x: x[0],
                                   reverse=True)
            if sorted_convos:
                latest_convo = sorted_convos[0][1]
                is_owner = latest_convo.get("is_owner", False)
                user_type = "👤 Regular user" if is_owner else "👤 Regular user"
                summary.append(f"User {user_id} ({user_type}):")
                summary.append(f"Last interaction: {latest_convo['message']}")
                summary.append(f"My response: {latest_convo['response']}\n")

        if not summary:
            return "No previous users in memory."

        return "\n".join(summary)

    def get_user_personality(self, user_id: str) -> str:
        """Analyze user's personality based on past interactions"""
        conversations = self.get_recent_conversations(user_id)
        if not conversations:
            return "No previous interaction data"

        # Count message characteristics
        total_msgs = len(conversations)
        polite_count = sum(1 for conv in conversations if any(
            word in conv['message'].lower()
            for word in ['please', 'thank', 'thanks', 'kind']))
        question_count = sum(1 for conv in conversations
                             if '?' in conv['message'])

        # Simple personality analysis
        traits = []
        if polite_count / total_msgs > 0.3:
            traits.append("generally polite")
        if question_count / total_msgs > 0.5:
            traits.append("very curious")
        if len(traits) == 0:
            traits.append("neutral personality")

        return ", ".join(traits)

    def add_instruction(self, user_id: str, instruction: str, is_permanent: bool = True):
        """Store user instructions with context"""
        if "instructions" not in self.memory_data:
            self.memory_data["instructions"] = {}
            
        if user_id not in self.memory_data["instructions"]:
            self.memory_data["instructions"][user_id] = []
            
        instruction_data = {
            "instruction": instruction,
            "timestamp": datetime.now().isoformat(),
            "is_permanent": is_permanent,
            "last_used": None,
            "usage_count": 0,
            "context": {
                "user_state": self._get_user_state(user_id),
                "conversation_context": self._get_conversation_context(user_id),
                "emotional_state": self._get_emotional_context()
            }
        }
        
        self.memory_data["instructions"][user_id].append(instruction_data)
        self._save_memory()

    def add_behavior_note(self, note: str):
        """Store general behavior notes and personality traits"""
        if "behavior_notes" not in self.memory_data:
            self.memory_data["behavior_notes"] = []

        timestamp = datetime.now().isoformat()
        self.memory_data["behavior_notes"].append({
            "timestamp": timestamp,
            "note": note
        })
        self._save_memory()

    def get_important_instructions(self, user_id: str = None) -> str:
        """Get summary of important instructions, optionally filtered by user"""
        if "instructions" not in self.memory_data:
            return "No stored instructions."

        summary = []
        instructions = self.memory_data["instructions"]

        if user_id:
            if user_id not in instructions:
                return "No instructions from this user."
            user_instructions = instructions[user_id]
            summary.append(f"Instructions from user {user_id}:")
            for inst in sorted(user_instructions,
                               key=lambda x: x["timestamp"],
                               reverse=True)[:5]:
                timestamp = datetime.fromisoformat(
                    inst["timestamp"]).strftime("%Y-%m-%d")
                summary.append(
                    f"[{timestamp}] {'👑 ' if inst['is_owner'] else ''}Instruction: {inst['instruction']}"
                )
        else:
            # Get most recent instructions from all users
            all_instructions = []
            for uid, user_instructions in instructions.items():
                for inst in user_instructions:
                    all_instructions.append((uid, inst))

            sorted_instructions = sorted(all_instructions,
                                         key=lambda x: x[1]["timestamp"],
                                         reverse=True)[:10]

            for uid, inst in sorted_instructions:
                timestamp = datetime.fromisoformat(
                    inst["timestamp"]).strftime("%Y-%m-%d")
                user_type = " Owner" if inst["is_owner"] else "User"
                summary.append(
                    f"[{timestamp}] {user_type} {uid}: {inst['instruction']}"
                )

        return "\n".join(summary)

    def get_behavior_summary(self) -> str:
        """Get summary of Bella's learned behaviors and personality traits"""
        if "behavior_notes" not in self.memory_data:
            return "No behavior notes stored."

        notes = self.memory_data["behavior_notes"]
        recent_notes = sorted(notes,
                              key=lambda x: x["timestamp"],
                              reverse=True)[:5]

        summary = ["Recent behavior notes:"]
        for note in recent_notes:
            timestamp = datetime.fromisoformat(
                note["timestamp"]).strftime("%Y-%m-%d")
            summary.append(f"[{timestamp}] {note['note']}")

        return "\n".join(summary)

    def add_owner_command(self, command: str, permanent: bool = True):
        """Store permanent commands from the owner"""
        if "owner_commands" not in self.memory_data:
            self.memory_data["owner_commands"] = {
                "permanent": [],
                "temporary": []
            }

        timestamp = datetime.now().isoformat()
        command_data = {
            "timestamp": timestamp,
            "command": command,
            "active": True
        }

        if permanent:
            self.memory_data["owner_commands"]["permanent"].append(
                command_data)
        else:
            self.memory_data["owner_commands"]["temporary"].append(
                command_data)

        self._save_memory()

    def get_active_owner_commands(self) -> str:
        """Get all active commands from the owner"""
        if "owner_commands" not in self.memory_data:
            return "No owner commands stored."

        summary = []

        # Get permanent commands
        permanent = self.memory_data["owner_commands"].get("permanent", [])
        if permanent:
            summary.append("🔒 Permanent Commands:")
            for cmd in permanent:
                if cmd.get("active", True):
                    timestamp = datetime.fromisoformat(
                        cmd["timestamp"]).strftime("%Y-%m-%d")
                    summary.append(f"[{timestamp}] {cmd['command']}")

        # Get temporary commands
        temporary = self.memory_data["owner_commands"].get("temporary", [])
        if temporary:
            if summary:  # Add spacing if there were permanent commands
                summary.append("")
            summary.append("⏳ Temporary Commands:")
            for cmd in temporary:
                if cmd.get("active", True):
                    timestamp = datetime.fromisoformat(
                        cmd["timestamp"]).strftime("%Y-%m-%d")
                    summary.append(f"[{timestamp}] {cmd['command']}")

        return "\n".join(summary) if summary else "No active owner commands."

    def add_punishment_rule(self,
                            target_id: str,
                            punishment_type: str,
                            duration: int = None):
        """Store permanent punishment rules set by owner"""
        if "punishment_rules" not in self.memory_data:
            self.memory_data["punishment_rules"] = {}

        timestamp = datetime.now().isoformat()
        self.memory_data["punishment_rules"][target_id] = {
            "timestamp": timestamp,
            "type": punishment_type,  # 'ban', 'kick', or 'timeout'
            "duration": duration,  # in minutes for timeout, None for ban/kick
            "active": True
        }
        self._save_memory()

    def get_punishment_rule(self, user_id: str) -> Optional[Dict]:
        """Get active punishment rule for a user if it exists"""
        if "punishment_rules" not in self.memory_data:
            return None

        rule = self.memory_data["punishment_rules"].get(user_id)
        if rule and rule.get("active", True):
            return rule
        return None

    def remove_punishment_rule(self, user_id: str):
        """Remove punishment rule for a user"""
        if "punishment_rules" in self.memory_data:
            if user_id in self.memory_data["punishment_rules"]:
                del self.memory_data["punishment_rules"][user_id]
                self._save_memory()

    def get_active_punishments_summary(self) -> str:
        """Get summary of all active punishments"""
        if "punishment_rules" not in self.memory_data:
            return "No active punishments."

        summary = []
        for user_id, rule in self.memory_data["punishment_rules"].items():
            if rule.get("active", True):
                punishment_type = rule["type"]
                duration = f" for {rule['duration']} minutes" if rule.get(
                    "duration") else ""
                summary.append(f"User {user_id}: {punishment_type}{duration}")

        return "\n".join(summary) if summary else "No active punishments."

    def add_behavior_rule(self, target_id: str, behavior: str, is_owner_command: bool = True):
        """Store behavior rules for specific users with treatment types"""
        if "behavior_rules" not in self.memory_data:
            self.memory_data["behavior_rules"] = {}

        timestamp = datetime.now().isoformat()
        if target_id not in self.memory_data["behavior_rules"]:
            self.memory_data["behavior_rules"][target_id] = []

        # Determine behavior type from command
        behavior_lower = behavior.lower()
        if any(phrase in behavior_lower for phrase in ["not behave", "don't behave", "be mean", "be rude"]):
            behavior_type = "hostile"
        elif any(phrase in behavior_lower for phrase in ["behave", "be nice", "be kind", "be good"]):
            behavior_type = "friendly"
        else:
            behavior_type = "neutral"

        # Deactivate previous rules for this user
        for rule in self.memory_data["behavior_rules"][target_id]:
            rule["active"] = False

        self.memory_data["behavior_rules"][target_id].append({
            "timestamp": timestamp,
            "behavior": behavior,
            "behavior_type": behavior_type,
            "is_owner_command": is_owner_command,
            "active": True
        })
        self._save_memory()

    def get_user_behavior_rules(self, user_id: str) -> str:
        """Get active behavior rules for a specific user"""
        if "behavior_rules" not in self.memory_data:
            return "No behavior rules."

        rules = self.memory_data["behavior_rules"].get(user_id, [])
        active_rules = [rule for rule in rules if rule.get("active", True)]

        if not active_rules:
            return "No active behavior rules."

        return "\n".join(f"- {rule['behavior']}" for rule in active_rules)

    def get_user_behavior_type(self, user_id: str) -> str:
        """Get the current behavior type for a user"""
        if "behavior_rules" not in self.memory_data:
            return "neutral"

        rules = self.memory_data["behavior_rules"].get(user_id, [])
        active_rules = [rule for rule in rules if rule.get("active", True)]
        
        if not active_rules:
            return "neutral"
        
        # Get most recent active rule
        latest_rule = max(active_rules, key=lambda x: x["timestamp"])
        return latest_rule.get("behavior_type", "neutral")

    def clear_all_memory(self):
        """Clear all stored memory and reset to initial state"""
        self.memory_data = {
            "users": {},
            "conversations": {},
            "instructions": {},
            "behavior_notes": [],
            "owner_commands": {
                "permanent": [],
                "temporary": []
            },
            "punishment_rules": {},
            "behavior_rules": {},
            "last_cleaned": datetime.now().isoformat()
        }
        self._save_memory()

    def add_analytics_data(self):
        """Add analytics tracking to memory structure"""
        if "analytics" not in self.memory_data:
            self.memory_data["analytics"] = {
                "user_engagement": {},      # Track user interaction frequency
                "command_usage": {},        # Track command usage statistics
                "response_metrics": {},     # Track response effectiveness
                "error_logs": [],          # Track errors and issues
                "performance_metrics": {}   # Track response times and system performance
            }

    def manage_user_reputation(self, user_id: str, action: str, value: int = 1):
        """Track user reputation based on interactions"""
        if "user_reputation" not in self.memory_data:
            self.memory_data["user_reputation"] = {}
        
        if user_id not in self.memory_data["user_reputation"]:
            self.memory_data["user_reputation"][user_id] = {
                "score": 0,
                "history": [],
                "badges": [],
                "warnings": 0
            }
        
        user_rep = self.memory_data["user_reputation"][user_id]
        timestamp = datetime.now().isoformat()
        
        if action == "positive":
            user_rep["score"] += value
        elif action == "negative":
            user_rep["score"] -= value
            
        user_rep["history"].append({
            "timestamp": timestamp,
            "action": action,
            "value": value
        })
        
        self._save_memory()

    def create_backup(self):
        """Create timestamped backup of memory"""
        backup_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"backup_{backup_time}_bella_memory.json"
        
        with open(backup_file, 'w') as f:
            json.dump(self.memory_data, f, indent=4)
        
        # Keep track of backups
        if "backups" not in self.memory_data:
            self.memory_data["backups"] = []
        
        self.memory_data["backups"].append({
            "timestamp": datetime.now().isoformat(),
            "filename": backup_file
        })
        self._save_memory()

    def restore_from_backup(self, backup_file: str):
        """Restore memory from backup"""
        try:
            with open(backup_file, 'r') as f:
                self.memory_data = json.load(f)
            self._save_memory()
            return True
        except Exception as e:
            print(f"Restore failed: {str(e)}")
            return False

    def optimize_memory(self):
        """Optimize memory usage by compressing old data"""
        for user_id in self.memory_data["conversations"]:
            conversations = self.memory_data["conversations"][user_id]
            if len(conversations) > 100:  # Threshold for optimization
                # Summarize old conversations
                old_convos = dict(sorted(conversations.items())[:50])  # Get oldest 50
                summary = self._generate_conversation_summary(old_convos)
                
                # Replace old conversations with summary
                new_convos = dict(sorted(conversations.items())[50:])  # Keep newest 50
                self.memory_data["conversations"][user_id] = new_convos
                
                # Store summary
                if "conversation_summaries" not in self.memory_data:
                    self.memory_data["conversation_summaries"] = {}
                if user_id not in self.memory_data["conversation_summaries"]:
                    self.memory_data["conversation_summaries"][user_id] = []
                
                self.memory_data["conversation_summaries"][user_id].append({
                    "period": f"{min(old_convos.keys())} to {max(old_convos.keys())}",
                    "summary": summary
                })

    def add_emotional_state(self, emotion: str, intensity: int, thought: str):
        """Track Bella's emotional state and unfiltered thoughts"""
        if "emotional_states" not in self.memory_data:
            self.memory_data["emotional_states"] = []
            
        timestamp = datetime.now().isoformat()
        self.memory_data["emotional_states"].append({
            "timestamp": timestamp,
            "emotion": emotion,        # e.g., "angry", "happy", "sassy"
            "intensity": intensity,    # 1-10 scale
            "raw_thought": thought,    # Unfiltered thought
            "is_expressed": False      # Track if this thought was expressed
        })
        self._save_memory()
    
    def get_current_emotional_state(self) -> Optional[Dict]:
        """Get Bella's current emotional state and thoughts"""
        if "emotional_states" not in self.memory_data or not self.memory_data["emotional_states"]:
            return None
            
        return self.memory_data["emotional_states"][-1]
    
    def get_unfiltered_response(self, context: str) -> Optional[str]:
        """Generate an unfiltered response based on emotional state"""
        current_state = self.get_current_emotional_state()
        if not current_state:
            return None
            
        emotion = current_state["emotion"]
        intensity = current_state["intensity"]
        
        # Return raw thoughts if intensity is high enough
        if intensity > 7:
            return current_state["raw_thought"]
            
        return None

    def add_memorable_phrase(self, phrase: str, context: str, impact_level: int):
        """Store memorable phrases and their context"""
        if "memorable_phrases" not in self.memory_data:
            self.memory_data["memorable_phrases"] = []
            
        timestamp = datetime.now().isoformat()
        self.memory_data["memorable_phrases"].append({
            "timestamp": timestamp,
            "phrase": phrase,
            "context": context,
            "impact_level": impact_level,  # 1-10 scale
            "usage_count": 0,
            "last_used": None
        })
        self._save_memory()
    
    def get_relevant_phrase(self, context: str) -> Optional[str]:
        """Get a relevant stored phrase based on context"""
        if "memorable_phrases" not in self.memory_data:
            return None
            
        phrases = self.memory_data["memorable_phrases"]
        relevant_phrases = [
            p for p in phrases 
            if any(word in context.lower() for word in p["context"].lower().split())
        ]
        
        if relevant_phrases:
            chosen = max(relevant_phrases, key=lambda x: x["impact_level"])
            chosen["usage_count"] += 1
            chosen["last_used"] = datetime.now().isoformat()
            self._save_memory()
            return chosen["phrase"]
            
        return None

    def add_message_pattern(self, user_id: str, pattern_type: str, content: str):
        """Track recurring message patterns from users"""
        if "message_patterns" not in self.memory_data:
            self.memory_data["message_patterns"] = {}
            
        if user_id not in self.memory_data["message_patterns"]:
            self.memory_data["message_patterns"][user_id] = {
                "greeting_patterns": [],
                "farewell_patterns": [],
                "question_patterns": [],
                "reaction_patterns": [],
                "common_phrases": {}
            }
            
        patterns = self.memory_data["message_patterns"][user_id]
        
        if pattern_type == "common_phrase":
            if content in patterns["common_phrases"]:
                patterns["common_phrases"][content] += 1
            else:
                patterns["common_phrases"][content] = 1
        else:
            pattern_list = patterns.get(f"{pattern_type}_patterns")
            if pattern_list is not None and content not in pattern_list:
                pattern_list.append(content)
                
        self._save_memory()

    def analyze_conversation_style(self, user_id: str) -> Dict:
        """Analyze user's conversation style based on patterns"""
        if user_id not in self.memory_data.get("message_patterns", {}):
            return {}
            
        patterns = self.memory_data["message_patterns"][user_id]
        
        style_analysis = {
            "formality_level": self._calculate_formality(patterns),
            "preferred_greetings": patterns["greeting_patterns"][:3],
            "common_phrases": sorted(
                patterns["common_phrases"].items(),
                key=lambda x: x[1],
                reverse=True
            )[:5],
            "question_frequency": len(patterns["question_patterns"]),
            "conversation_traits": self._analyze_conversation_traits(patterns)
        }
        
        return style_analysis

    def _determine_message_type(self, message: str) -> str:
        """Determine the type of message"""
        message_lower = message.lower()
        
        if any(cmd in message_lower for cmd in ["ban", "kick", "timeout", "behave"]):
            return "command"
        elif "?" in message:
            return "question"
        elif any(word in message_lower for word in ["hi", "hello", "hey"]):
            return "greeting"
        elif any(word in message_lower for word in ["bye", "goodbye", "cya"]):
            return "farewell"
        elif any(word in message_lower for word in ["thanks", "thank you", "thx"]):
            return "gratitude"
        return "conversation"

    def _analyze_sentiment(self, message: str) -> str:
        """Analyze the sentiment of a message"""
        message_lower = message.lower()
        
        # Very positive indicators
        if any(phrase in message_lower for phrase in [
            "love you", "amazing", "wonderful", "excellent", "perfect"
        ]):
            return "very_positive"
            
        # Positive indicators
        if any(word in message_lower for word in [
            "good", "nice", "thanks", "please", "kind", "happy", "great"
        ]):
            return "positive"
            
        # Very negative indicators
        if any(phrase in message_lower for phrase in [
            "hate you", "stupid", "idiot", "shut up", "fuck"
        ]):
            return "very_negative"
            
        # Negative indicators
        if any(word in message_lower for word in [
            "bad", "mean", "rude", "angry", "sad", "hate", "dislike"
        ]):
            return "negative"
            
        return "neutral"

    def _get_user_state(self, user_id: str) -> Dict:
        """Get the current state of a user"""
        return {
            "behavior_type": self.get_user_behavior_type(user_id),
            "recent_interactions": len(self.get_recent_conversations(user_id)),
            "has_active_punishment": bool(self.get_punishment_rule(user_id))
        }

    def _get_conversation_chain(self, user_id: str) -> List[Dict]:
        """Get the recent conversation chain"""
        return self.get_recent_conversations(user_id, limit=3)

    def _get_active_rules(self, user_id: str) -> Dict:
        """Get all active rules for a user"""
        return {
            "behavior": self.get_user_behavior_rules(user_id),
            "punishment": self.get_punishment_rule(user_id)
        }

    def _get_server_load(self) -> str:
        """Get current server load status"""
        # This is a placeholder - you could implement actual server metrics
        return "normal"

    def _calculate_formality(self, patterns: Dict) -> str:
        """Calculate the formality level of user's language"""
        formal_indicators = len([
            phrase for phrase in patterns.get("common_phrases", {})
            if any(word in phrase.lower() for word in 
                ["please", "thank", "would", "could", "kindly"])
        ])
        
        informal_indicators = len([
            phrase for phrase in patterns.get("common_phrases", {})
            if any(word in phrase.lower() for word in 
                ["hey", "sup", "yo", "lol", "omg"])
        ])
        
        if formal_indicators > informal_indicators:
            return "formal"
        elif informal_indicators > formal_indicators:
            return "informal"
        return "neutral"

    def _analyze_conversation_traits(self, patterns: Dict) -> List[str]:
        """Analyze conversation traits based on patterns"""
        traits = []
        
        # Analyze greeting patterns
        if len(patterns["greeting_patterns"]) > 3:
            traits.append("consistently_polite")
            
        # Analyze question frequency
        if len(patterns["question_patterns"]) > 5:
            traits.append("inquisitive")
            
        # Analyze common phrases
        common_phrases = patterns.get("common_phrases", {})
        if len(common_phrases) > 10:
            traits.append("conversational")
            
        return traits

    def verify_memory_integrity(self) -> bool:
        """Verify memory structure is intact"""
        required_keys = [
            "users", "conversations", "instructions", 
            "behavior_notes", "owner_commands", "punishment_rules",
            "behavior_rules", "emotional_states", "analytics",
            "user_reputation", "conversation_summaries",
            "memorable_phrases", "message_patterns"
        ]
        
        missing_keys = [key for key in required_keys if key not in self.memory_data]
        
        if missing_keys:
            print(f"Warning: Missing memory keys: {missing_keys}")
            return False
        return True

    def _extract_keywords(self, message: str) -> List[str]:
        """Extract important keywords from message"""
        # Simple keyword extraction based on common patterns
        keywords = []
        words = message.lower().split()
        
        # Extract potential keywords (nouns, verbs, etc.)
        for word in words:
            if len(word) > 3 and word not in ["this", "that", "have", "what", "when", "where"]:
                keywords.append(word)
        
        return list(set(keywords))

    def _identify_topics(self, message: str) -> List[str]:
        """Identify conversation topics"""
        topics = []
        message_lower = message.lower()
        
        # Define topic categories
        topic_keywords = {
            "greeting": ["hi", "hello", "hey"],
            "farewell": ["bye", "goodbye", "cya"],
            "command": ["ban", "kick", "timeout", "behave"],
            "emotion": ["happy", "sad", "angry", "love", "hate"],
            "question": ["what", "why", "how", "when", "where"],
            "instruction": ["make", "do", "can you", "please", "help"],
            "feedback": ["good", "bad", "nice", "terrible"]
        }
        
        for topic, keywords in topic_keywords.items():
            if any(word in message_lower for word in keywords):
                topics.append(topic)
                
        return topics

    def _find_references(self, message: str) -> Dict:
        """Find references to previous conversations or instructions"""
        references = {
            "users": [],
            "commands": [],
            "previous_conversations": [],
            "instructions": []
        }
        
        # Look for user mentions
        mention_pattern = r'<@!?(\d+)>'
        references["users"] = re.findall(mention_pattern, message)
        
        # Look for command references
        command_pattern = r'!(\w+)'
        references["commands"] = re.findall(command_pattern, message)
        
        # Look for instruction references
        if "instructions" in self.memory_data:
            for instruction in self.memory_data["instructions"].values():
                for inst in instruction:
                    if inst["instruction"].lower() in message.lower():
                        references["instructions"].append(inst)
        
        return references

    def _get_emotional_context(self) -> Dict:
        """Get current emotional context"""
        current_state = self.get_current_emotional_state()
        if not current_state:
            return {"emotion": "neutral", "intensity": 0}
            
        return {
            "emotion": current_state["emotion"],
            "intensity": current_state["intensity"],
            "recent_emotions": self._get_recent_emotions(5)  # Get last 5 emotions
        }

    def _find_related_memories(self, message: str, user_id: str) -> List[Dict]:
        """Find memories related to current conversation"""
        related = []
        keywords = self._extract_keywords(message)
        
        # Search through past conversations
        if user_id in self.memory_data.get("conversations", {}):
            for timestamp, convo in self.memory_data["conversations"][user_id].items():
                convo_keywords = self._extract_keywords(convo["message"])
                if any(keyword in convo_keywords for keyword in keywords):
                    related.append({
                        "type": "conversation",
                        "timestamp": timestamp,
                        "content": convo["message"]
                    })
        
        return related[:5]  # Return top 5 related memories

    def _find_relevant_instructions(self, message: str) -> List[Dict]:
        """Find instructions relevant to the current message"""
        relevant = []
        keywords = self._extract_keywords(message)
        
        # Search through all instructions
        if "instructions" in self.memory_data:
            for user_id, instructions in self.memory_data["instructions"].items():
                for instruction in instructions:
                    # Check if instruction content matches any keywords
                    instruction_keywords = self._extract_keywords(instruction["instruction"])
                    if any(keyword in instruction_keywords for keyword in keywords):
                        relevant.append({
                            "instruction": instruction["instruction"],
                            "timestamp": instruction["timestamp"],
                            "is_owner": instruction.get("is_owner", False),
                            "usage_count": instruction.get("usage_count", 0)
                        })
        
        # Sort by usage count and timestamp, prioritize owner instructions
        relevant.sort(key=lambda x: (
            x["is_owner"],
            x["usage_count"],
            x["timestamp"]
        ), reverse=True)
        
        return relevant[:3]  # Return top 3 most relevant instructions

    def _get_recent_emotions(self, limit: int = 5) -> List[Dict]:
        """Get recent emotional states"""
        if "emotional_states" not in self.memory_data:
            return []
            
        recent = sorted(
            self.memory_data["emotional_states"],
            key=lambda x: x["timestamp"],
            reverse=True
        )[:limit]
        
        return [{
            "emotion": state["emotion"],
            "intensity": state["intensity"],
            "timestamp": state["timestamp"]
        } for state in recent]

    def _process_conversation_patterns(self, user_id: str, message: str, context: Dict):
        """Process and store conversation patterns"""
        message_lower = message.lower()
        
        # Process greeting patterns
        if any(word in message_lower for word in ["hi", "hello", "hey"]):
            self.add_message_pattern(user_id, "greeting_patterns", message)
        elif any(word in message_lower for word in ["bye", "goodbye", "cya"]):
            self.add_message_pattern(user_id, "farewell_patterns", message)
        elif "?" in message:
            self.add_message_pattern(user_id, "question_patterns", message)
            
        # Store memorable phrases if message has high impact
        if context["sentiment"] in ["very_positive", "very_negative"]:
            self.add_memorable_phrase(
                message,
                context["message_type"],
                8 if context["sentiment"] == "very_positive" else 9
            )
            
        # Track common phrases (3+ words)
        words = message.split()
        if len(words) >= 3:
            for i in range(len(words)-2):
                phrase = " ".join(words[i:i+3])
                self.add_message_pattern(user_id, "common_phrase", phrase)
        
        self._clean_old_memories()

    def add_user_preference(self, user_id: str, preference_type: str, value: str):
        """Track user preferences and likes/dislikes"""
        if "user_preferences" not in self.memory_data:
            self.memory_data["user_preferences"] = {}
            
        if user_id not in self.memory_data["user_preferences"]:
            self.memory_data["user_preferences"][user_id] = {
                "topics": [],
                "response_style": "default",
                "language": "english",
                "likes": [],
                "dislikes": []
            }
            
        preferences = self.memory_data["user_preferences"][user_id]
        
        if preference_type in preferences:
            if isinstance(preferences[preference_type], list):
                if value not in preferences[preference_type]:
                    preferences[preference_type].append(value)
            else:
                preferences[preference_type] = value
                
        self._save_memory()

    def update_interaction_metrics(self, user_id: str):
        """Update user interaction metrics"""
        if "interaction_metrics" not in self.memory_data:
            self.memory_data["interaction_metrics"] = {}
            
        if user_id not in self.memory_data["interaction_metrics"]:
            self.memory_data["interaction_metrics"][user_id] = {
                "last_interaction": None,
                "interaction_count": 0,
                "average_response_time": 0
            }
            
        metrics = self.memory_data["interaction_metrics"][user_id]
        current_time = datetime.now().isoformat()
        
        if metrics["last_interaction"]:
            # Calculate time since last interaction
            last_time = datetime.fromisoformat(metrics["last_interaction"])
            current = datetime.fromisoformat(current_time)
            time_diff = (current - last_time).total_seconds()
            
            # Update average response time
            metrics["average_response_time"] = (
                (metrics["average_response_time"] * metrics["interaction_count"] + time_diff) /
                (metrics["interaction_count"] + 1)
            )
            
        metrics["last_interaction"] = current_time
        metrics["interaction_count"] += 1
        
        self._save_memory()

    def update_relationship_status(self, user_id: str, status: str):
        """Update relationship status with a user"""
        if "relationships" not in self.memory_data:
            self.memory_data["relationships"] = {}
            
        self.memory_data["relationships"][user_id] = {
            "status": status,
            "last_updated": datetime.now().isoformat(),
            "history": self.memory_data["relationships"].get(user_id, {}).get("history", [])
        }
        
        # Add to history
        history_entry = {
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "context": self._get_current_context()
        }
        
        self.memory_data["relationships"][user_id]["history"] = \
            self.memory_data["relationships"][user_id].get("history", [])[-4:] + [history_entry]
        
        self._save_memory()

    def _get_current_context(self) -> Dict:
        """Get current context for relationship updates"""
        return {
            "time": datetime.now().isoformat(),
            "active_emotional_state": self._get_current_emotional_state(),
            "recent_interactions": self._get_recent_interactions_summary()
        }

    def _get_current_emotional_state(self) -> Dict:
        """Get current emotional state"""
        if not self.memory_data.get("emotional_states"):
            return {"emotion": "neutral", "intensity": 0}
            
        current_states = sorted(
            self.memory_data["emotional_states"],
            key=lambda x: x["timestamp"],
            reverse=True
        )
        
        return current_states[0] if current_states else {"emotion": "neutral", "intensity": 0}

    def _get_recent_interactions_summary(self) -> Dict:
        """Get summary of recent interactions"""
        recent_interactions = {
            "positive": 0,
            "negative": 0,
            "neutral": 0,
            "total": 0
        }
        
        for user_id, interactions in self.memory_data.get("conversations", {}).items():
            for timestamp, interaction in interactions.items():
                if datetime.now() - datetime.fromisoformat(timestamp) <= timedelta(hours=24):
                    sentiment = interaction.get("context", {}).get("sentiment", "neutral")
                    if "positive" in sentiment:
                        recent_interactions["positive"] += 1
                    elif "negative" in sentiment:
                        recent_interactions["negative"] += 1
                    else:
                        recent_interactions["neutral"] += 1
                    recent_interactions["total"] += 1
                    
        return recent_interactions

    def get_relationship_status(self, user_id: str) -> Dict:
        """Get the relationship status with a user"""
        if "relationships" not in self.memory_data:
            self.memory_data["relationships"] = {}
            
        if user_id not in self.memory_data["relationships"]:
            return {"status": "neutral", "last_updated": datetime.now().isoformat()}
            
        return self.memory_data["relationships"][user_id]

    def get_user_name(self, user_id: str) -> str:
        """Get user's name or default to 'User'"""
        user_info = self.get_user_info(user_id)
        return user_info["personal_info"]["name"] or "User"

    def get_conversation_chain(self, user_id: str, limit: int = 5) -> List[Dict]:
        """Get recent conversation chain with context"""
        if user_id not in self.memory_data.get("conversations", {}):
            return []
            
        conversations = self.memory_data["conversations"][user_id]
        sorted_convos = sorted(conversations.items(), key=lambda x: x[1]["timestamp"], reverse=True)
        
        chain = []
        for _, convo in sorted_convos[:limit]:
            chain.append({
                "message": convo["message"],
                "response": convo["response"],
                "context": convo.get("context", {}),
                "timestamp": convo["timestamp"]
            })
            
        return chain

    def get_active_instructions(self, user_id: str) -> List[Dict]:
        """Get all active instructions for a user"""
        if user_id not in self.memory_data.get("instructions", {}):
            return []
            
        active_instructions = []
        for instruction in self.memory_data["instructions"][user_id]:
            if instruction["is_permanent"] or (
                instruction.get("expiry") and 
                datetime.fromisoformat(instruction["expiry"]) > datetime.now()
            ):
                active_instructions.append(instruction)
                
        return active_instructions

    def _get_conversation_context(self, user_id: str) -> Dict:
        """Get context from recent conversations"""
        recent_convos = self.get_conversation_chain(user_id, limit=3)
        topics = set()
        sentiment = "neutral"
        
        for convo in recent_convos:
            if "context" in convo:
                topics.update(convo["context"].get("topics", []))
                # Update sentiment based on most recent significant emotion
                if convo["context"].get("sentiment") in ["very_positive", "very_negative"]:
                    sentiment = convo["context"]["sentiment"]
                    break
                    
        return {
            "recent_topics": list(topics),
            "overall_sentiment": sentiment,
            "conversation_count": len(recent_convos)
        }

    def add_media_interaction(self, user_id: str, media_type: str, context: Dict):
        """Track media interactions"""
        if "media_interactions" not in self.memory_data:
            self.memory_data["media_interactions"] = {
                "images": {},
                "voice_messages": {},
                "last_processed": None
            }
            
        if user_id not in self.memory_data["media_interactions"][media_type]:
            self.memory_data["media_interactions"][media_type][user_id] = []
            
        interaction_data = {
            "timestamp": datetime.now().isoformat(),
            "context": context
        }
        
        self.memory_data["media_interactions"][media_type][user_id].append(interaction_data)
        self.memory_data["media_interactions"]["last_processed"] = datetime.now().isoformat()
        
        self._save_memory()

    def add_owner_note_about_user(self, target_user_id: str, note: str, context: str = None):
        """Store owner's comments/notes about specific users"""
        if "user_notes" not in self.memory_data:
            self.memory_data["user_notes"] = {}
            
        if target_user_id not in self.memory_data["user_notes"]:
            self.memory_data["user_notes"][target_user_id] = []
            
        note_entry = {
            "timestamp": datetime.now().isoformat(),
            "note": note,
            "context": context,
            "active": True
        }
        
        self.memory_data["user_notes"][target_user_id].append(note_entry)
        self._save_memory()
        
    def get_owner_notes_about_user(self, user_id: str) -> List[Dict]:
        """Get all active notes about a user"""
        if "user_notes" not in self.memory_data or user_id not in self.memory_data["user_notes"]:
            return []
            
        return [note for note in self.memory_data["user_notes"][user_id] if note["active"]]

    def get_user_context_summary(self, user_id: str) -> str:
        """Get a summary of all context about a user including owner's notes"""
        notes = self.get_owner_notes_about_user(user_id)
        if not notes:
            return ""
            
        recent_notes = sorted(notes, key=lambda x: x["timestamp"], reverse=True)[:3]
        return "\n".join([f"Owner said: {note['note']}" for note in recent_notes])

    def get_user_analytics(self, user_id: str) -> Dict:
        """Get analytics for specific user"""
        if user_id not in self.memory_data["analytics"]["user_engagement"]:
            return None
            
        analytics = self.memory_data["analytics"]["user_engagement"][user_id]
        return {
            "total_messages": analytics.get("total_messages", 0),
            "avg_length": round(analytics.get("avg_message_length", 0), 2),
            "sentiment": analytics.get("sentiment_distribution", {}),
            "active_hours": analytics.get("active_hours", {})
        }
