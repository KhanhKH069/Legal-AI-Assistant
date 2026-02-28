"""
HR AI Agent - Main Application Entry Point
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import logging

from langchain_core.messages import AIMessage, HumanMessage
from services.database import SQLDatabase

from agents.orchestrator import create_hr_agent_graph
from core.admin import AdminPanel
from core.gateway import APIGateway
from services.audit import AuditLogger
from utils.logger import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

class HRAgentApp:
    """Main HR Agent Application"""
    
    def __init__(self):
        logger.info("Initializing HR Agent...")
        
        self.sql_db = SQLDatabase()
        self.audit_logger = AuditLogger(self.sql_db)
        self.api_gateway = APIGateway(self.audit_logger)
        self.admin_panel = AdminPanel(self.sql_db)
        self.graph = create_hr_agent_graph()
        self.conversation_history = {}
        
        logger.info("✅ HR Agent initialized!")
    
    def chat(self, user_id: str, message: str, api_key: str = None) -> dict:
        """Process chat message"""
        
        gateway_response = self.api_gateway.process_request(user_id, message, api_key)
        
        if gateway_response['status'] != 'success':
            return gateway_response
        
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = []
        
        human_msg = HumanMessage(content=message)
        self.conversation_history[user_id].append(human_msg)
        
        initial_state = {
            "messages": self.conversation_history[user_id],
            "next": "",
            "user_intent": "",
            "user_id": user_id,
            "user_info": gateway_response['user_info']
        }
        
        try:
            result = self.graph.invoke(initial_state)
            
            if result["messages"]:
                last_message = result["messages"][-1]
                
                if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                    response_text = f"Intent: {result.get('user_intent', 'N/A')}\n\n"
                    for tool_call in last_message.tool_calls:
                        response_text += f"🔧 {tool_call['name']}\n"
                    response_text += f"\n{last_message.content if last_message.content else ''}"
                else:
                    response_text = last_message.content
                
                self.conversation_history[user_id].append(AIMessage(content=response_text))
                
                return {
                    'status': 'success',
                    'response': response_text,
                    'intent': result.get('user_intent', ''),
                    'user_id': user_id
                }
            else:
                return {
                    'status': 'error',
                    'message': 'No response generated',
                    'code': 500
                }
                
        except Exception as e:
            logger.error(f"Error: {str(e)}", exc_info=True)
            return {
                'status': 'error',
                'message': f'Error: {str(e)}',
                'code': 500
            }
    
    def reset_conversation(self, user_id: str):
        """Reset conversation"""
        if user_id in self.conversation_history:
            self.conversation_history[user_id] = []
            logger.info(f"Reset conversation for {user_id}")

def demo():
    """Run demo"""
    print("=" * 80)
    print("🏢 HR AI AGENT - Modular System")
    print("=" * 80)
    print("\n📊 Components:")
    print("  ✅ API Gateway")
    print("  ✅ Orchestrator")
    print("  ✅ Policy Agent")
    print("  ✅ Onboard Agent")
    print("  ✅ Shared Services")
    print("\n" + "=" * 80 + "\n")
    
    app = HRAgentApp()
    demo_user = "user001"
    
    questions = [
        "Công ty có bao nhiêu ngày phép?",
        "Nhân viên mới cần giấy tờ gì?",
        "Tôi làm 8 tháng full_time có bao nhiêu ngày phép?",
        "Checklist tuần đầu?",
    ]
    
    print("🎮 DEMO:\n")
    
    for i, q in enumerate(questions, 1):
        print(f"\n{'='*80}")
        print(f"❓ Q{i}: {q}")
        print("="*80 + "\n")
        
        response = app.chat(demo_user, q)
        
        if response['status'] == 'success':
            print(f"✅ Status: {response['status']}")
            print(f"🎯 Intent: {response['intent']}")
            print(f"\n💬 Response:\n{response['response']}\n")
        else:
            print(f"❌ Error: {response['message']}\n")
    
    print("\n" + "=" * 80)
    print("📊 Statistics")
    print("=" * 80)
    stats = app.admin_panel.get_statistics()
    print(f"\nTotal: {stats['total_requests']}")
    print(f"By Action: {stats['requests_by_action']}")
    
    print("\n" + "=" * 80)
    print("💬 Interactive Mode")
    print("=" * 80)
    print("\nCommands: 'stats', 'reset', 'quit'")
    print("=" * 80 + "\n")
    
    while True:
        try:
            user_input = input(f"👤 {demo_user}: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit']:
                print("\n👋 Goodbye!")
                break
            
            if user_input.lower() == 'reset':
                app.reset_conversation(demo_user)
                print("✅ Reset\n")
                continue
            
            if user_input.lower() == 'stats':
                stats = app.admin_panel.get_statistics()
                print(f"\n📊 {stats}\n")
                continue
            
            print()
            response = app.chat(demo_user, user_input)
            
            if response['status'] == 'success':
                print(f"💬 Agent: {response['response']}\n")
            else:
                print(f"❌ Error: {response['message']}\n")
                
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}\n")

if __name__ == "__main__":
    demo()
