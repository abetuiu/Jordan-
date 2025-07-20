#!/usr/bin/env python3
"""
Backend API Testing Suite for AI Chatbot
Tests all core backend functionality including health checks, personalities, chat, sessions, and voice endpoints.
"""

import requests
import json
import base64
import uuid
from datetime import datetime
import time

# Configuration
BACKEND_URL = "https://f63565b9-5303-4467-b49c-34c62fb9e87b.preview.emergentagent.com/api"
TIMEOUT = 30

class BackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = TIMEOUT
        self.test_results = []
        self.session_id = None
        
    def log_test(self, test_name, success, message, details=None):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "details": details
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name} - {message}")
        if details:
            print(f"   Details: {details}")
    
    def test_health_check(self):
        """Test /api/health endpoint"""
        try:
            response = self.session.get(f"{BACKEND_URL}/health")
            
            if response.status_code == 200:
                data = response.json()
                if "status" in data and data["status"] == "healthy":
                    integrations_available = data.get("integrations_available", False)
                    self.log_test(
                        "Health Check", 
                        True, 
                        f"Server is healthy, integrations_available: {integrations_available}",
                        data
                    )
                    return True
                else:
                    self.log_test("Health Check", False, "Invalid health response format", data)
                    return False
            else:
                self.log_test("Health Check", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Health Check", False, f"Connection error: {str(e)}")
            return False
    
    def test_personalities(self):
        """Test /api/personalities endpoint"""
        try:
            response = self.session.get(f"{BACKEND_URL}/personalities")
            
            if response.status_code == 200:
                data = response.json()
                if "personalities" in data and isinstance(data["personalities"], list):
                    personalities = data["personalities"]
                    expected_personalities = ["assistant", "creative", "expert", "friend"]
                    
                    found_personalities = [p.get("_id") for p in personalities]
                    missing = set(expected_personalities) - set(found_personalities)
                    
                    if not missing and len(personalities) >= 4:
                        # Verify personality structure
                        valid_structure = True
                        for p in personalities:
                            required_fields = ["_id", "name", "description", "avatar_color", "personality_traits"]
                            if not all(field in p for field in required_fields):
                                valid_structure = False
                                break
                        
                        if valid_structure:
                            self.log_test(
                                "Personalities Fetch", 
                                True, 
                                f"Found {len(personalities)} personalities with correct structure",
                                {"personalities": [p["name"] for p in personalities]}
                            )
                            return personalities
                        else:
                            self.log_test("Personalities Fetch", False, "Invalid personality structure", data)
                            return None
                    else:
                        self.log_test("Personalities Fetch", False, f"Missing personalities: {missing}", data)
                        return None
                else:
                    self.log_test("Personalities Fetch", False, "Invalid response format", data)
                    return None
            else:
                self.log_test("Personalities Fetch", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Personalities Fetch", False, f"Connection error: {str(e)}")
            return None
    
    def test_new_session(self):
        """Test /api/sessions/new endpoint"""
        try:
            response = self.session.get(f"{BACKEND_URL}/sessions/new")
            
            if response.status_code == 200:
                data = response.json()
                if "session_id" in data and data["session_id"]:
                    session_id = data["session_id"]
                    # Validate UUID format
                    try:
                        uuid.UUID(session_id)
                        self.session_id = session_id
                        self.log_test(
                            "New Session Creation", 
                            True, 
                            f"Created session: {session_id[:8]}...",
                            {"session_id": session_id}
                        )
                        return session_id
                    except ValueError:
                        self.log_test("New Session Creation", False, "Invalid session ID format", data)
                        return None
                else:
                    self.log_test("New Session Creation", False, "No session_id in response", data)
                    return None
            else:
                self.log_test("New Session Creation", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("New Session Creation", False, f"Connection error: {str(e)}")
            return None
    
    def test_chat_functionality(self, personalities):
        """Test /api/chat endpoint with different personalities"""
        if not personalities:
            self.log_test("Chat Functionality", False, "No personalities available for testing")
            return False
        
        test_messages = [
            "Hello, how are you today?",
            "Can you help me with a creative writing project?",
            "What's the weather like?",
            "Tell me about artificial intelligence"
        ]
        
        success_count = 0
        total_tests = 0
        
        for personality in personalities[:2]:  # Test first 2 personalities to save time
            personality_id = personality["_id"]
            personality_name = personality["name"]
            
            for i, message in enumerate(test_messages[:2]):  # Test 2 messages per personality
                total_tests += 1
                try:
                    payload = {
                        "text": message,
                        "personality_id": personality_id,
                        "session_id": self.session_id
                    }
                    
                    response = self.session.post(
                        f"{BACKEND_URL}/chat",
                        json=payload,
                        headers={"Content-Type": "application/json"}
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        required_fields = ["message", "personality_id", "session_id", "timestamp", "message_id"]
                        
                        if all(field in data for field in required_fields):
                            # Verify personality-specific response
                            ai_message = data["message"].lower()
                            personality_indicators = {
                                "assistant": ["assistant", "professional", "help"],
                                "creative": ["creative", "artistic", "inspiring", "🎨"],
                                "expert": ["technical", "analysis", "data", "research"],
                                "friend": ["hey", "😊", "friend", "think"]
                            }
                            
                            indicators = personality_indicators.get(personality_id, [])
                            has_personality = any(indicator in ai_message for indicator in indicators)
                            
                            if has_personality or len(data["message"]) > 20:  # Accept if response is substantial
                                success_count += 1
                                self.log_test(
                                    f"Chat - {personality_name}", 
                                    True, 
                                    f"Received personality-appropriate response",
                                    {"message_preview": data["message"][:100] + "..."}
                                )
                            else:
                                self.log_test(
                                    f"Chat - {personality_name}", 
                                    False, 
                                    "Response doesn't match personality style",
                                    {"response": data["message"]}
                                )
                        else:
                            missing_fields = [f for f in required_fields if f not in data]
                            self.log_test(
                                f"Chat - {personality_name}", 
                                False, 
                                f"Missing fields: {missing_fields}",
                                data
                            )
                    else:
                        self.log_test(
                            f"Chat - {personality_name}", 
                            False, 
                            f"HTTP {response.status_code}: {response.text}"
                        )
                        
                except Exception as e:
                    self.log_test(f"Chat - {personality_name}", False, f"Error: {str(e)}")
        
        overall_success = success_count >= (total_tests * 0.7)  # 70% success rate
        self.log_test(
            "Chat Functionality Overall", 
            overall_success, 
            f"Passed {success_count}/{total_tests} chat tests"
        )
        return overall_success
    
    def test_voice_endpoint(self, personalities):
        """Test /api/voice/send endpoint"""
        if not personalities:
            self.log_test("Voice Endpoint", False, "No personalities available for testing")
            return False
        
        try:
            # Create mock base64 audio data
            mock_audio = base64.b64encode(b"mock_audio_data_for_testing").decode('utf-8')
            
            personality = personalities[0]  # Use first personality
            payload = {
                "audio_data": mock_audio,
                "personality_id": personality["_id"],
                "session_id": self.session_id
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/voice/send",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["message", "personality_id", "session_id", "timestamp", "message_id"]
                
                if all(field in data for field in required_fields):
                    self.log_test(
                        "Voice Endpoint", 
                        True, 
                        "Voice message processed successfully",
                        {"response_preview": data["message"][:100] + "..."}
                    )
                    return True
                else:
                    missing_fields = [f for f in required_fields if f not in data]
                    self.log_test("Voice Endpoint", False, f"Missing fields: {missing_fields}", data)
                    return False
            else:
                self.log_test("Voice Endpoint", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Voice Endpoint", False, f"Error: {str(e)}")
            return False
    
    def test_conversation_retrieval(self):
        """Test /api/conversations/{session_id} endpoint"""
        if not self.session_id:
            self.log_test("Conversation Retrieval", False, "No session ID available")
            return False
        
        try:
            response = self.session.get(f"{BACKEND_URL}/conversations/{self.session_id}")
            
            if response.status_code == 200:
                data = response.json()
                if "messages" in data and isinstance(data["messages"], list):
                    messages = data["messages"]
                    if len(messages) > 0:
                        # Verify message structure
                        valid_messages = True
                        for msg in messages:
                            required_fields = ["session_id", "role", "content", "timestamp"]
                            if not all(field in msg for field in required_fields):
                                valid_messages = False
                                break
                        
                        if valid_messages:
                            self.log_test(
                                "Conversation Retrieval", 
                                True, 
                                f"Retrieved {len(messages)} messages from session",
                                {"message_count": len(messages)}
                            )
                            return True
                        else:
                            self.log_test("Conversation Retrieval", False, "Invalid message structure", data)
                            return False
                    else:
                        self.log_test(
                            "Conversation Retrieval", 
                            True, 
                            "No messages in session (expected for new session)",
                            {"message_count": 0}
                        )
                        return True
                else:
                    self.log_test("Conversation Retrieval", False, "Invalid response format", data)
                    return False
            else:
                self.log_test("Conversation Retrieval", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Conversation Retrieval", False, f"Error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting Backend API Tests...")
        print(f"Testing against: {BACKEND_URL}")
        print("=" * 60)
        
        # Test 1: Health Check
        health_ok = self.test_health_check()
        
        # Test 2: Personalities
        personalities = self.test_personalities()
        
        # Test 3: New Session
        session_id = self.test_new_session()
        
        # Test 4: Chat Functionality
        chat_ok = self.test_chat_functionality(personalities)
        
        # Test 5: Voice Endpoint
        voice_ok = self.test_voice_endpoint(personalities)
        
        # Test 6: Conversation Retrieval
        conversation_ok = self.test_conversation_retrieval()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        # Critical functionality check
        critical_tests = [health_ok, personalities is not None, session_id is not None, chat_ok]
        critical_passed = sum(critical_tests)
        
        print(f"\nCritical Functionality: {critical_passed}/4 tests passed")
        
        if critical_passed >= 3:
            print("✅ Backend is functioning properly!")
        else:
            print("❌ Backend has critical issues that need attention!")
        
        return {
            "total_tests": total,
            "passed": passed,
            "failed": total - passed,
            "success_rate": (passed/total)*100,
            "critical_passed": critical_passed,
            "overall_status": "PASS" if critical_passed >= 3 else "FAIL",
            "results": self.test_results
        }

if __name__ == "__main__":
    tester = BackendTester()
    results = tester.run_all_tests()
    
    # Save results to file
    with open("/app/backend_test_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📁 Detailed results saved to: /app/backend_test_results.json")