"""
Gemini API client for handling interactions with the Google AI API
"""
import os
import json
import logging
from typing import Dict, List, Optional, Any, Union
import google.generativeai as genai
from django.conf import settings

logger = logging.getLogger(__name__)

class GeminiClient:
    """
    Client class for interacting with the Gemini API
    """
    def __init__(self):
        """Initialize the Gemini client with API key from environment variables"""
        try:
            api_key = os.environ.get('GEMINI_API_KEY')
            if not api_key:
                raise ValueError("GEMINI_API_KEY not found in environment variables")
            
            # Cấu hình API key
            genai.configure(api_key=api_key)
            
            # Khởi tạo model
            self.model = genai.GenerativeModel('gemini-pro')
            logger.info("Gemini API client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini API client: {str(e)}")
            raise

    def generate_text_response(self, prompt: str, context: Optional[str] = None) -> str:
        """
        Generate a text response using Gemini API
        
        Args:
            prompt (str): The user's prompt/question
            context (Optional[str]): Additional context about the system
            
        Returns:
            str: The generated response
        """
        try:
            # Combine system context with user prompt if provided
            if context:
                full_prompt = f"{context}\n\nUser question: {prompt}"
            else:
                full_prompt = prompt
                
            response = self.model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            logger.error(f"Error generating response from Gemini API: {str(e)}")
            return f"Sorry, I encountered an error: {str(e)}"
    
    def generate_chat_response(self, history: List[Dict[str, str]], 
                               system_instructions: Optional[str] = None) -> str:
        """
        Generate a response for an ongoing conversation
        
        Args:
            history (List[Dict[str, str]]): List of message dictionaries with 'role' and 'content'
            system_instructions (Optional[str]): System instructions to guide the model
            
        Returns:
            str: The generated response
        """
        try:
            # Tạo một đối tượng chat session
            chat = self.model.start_chat(history=[])
            
            # Thêm system instructions nếu được cung cấp
            if system_instructions:
                chat.send_message(f"SYSTEM: {system_instructions}")
            
            # Thêm lịch sử trò chuyện
            for msg in history[:-1]:  # Không thêm tin nhắn cuối cùng của người dùng
                role = msg["role"]
                content = msg["content"]
                # Trong genai API mới, chúng ta gửi từng tin nhắn riêng lẻ
                chat.send_message(content)
            
            # Lấy tin nhắn cuối cùng của người dùng
            last_msg = history[-1] if history else {"content": ""}
            
            # Gửi tin nhắn cuối cùng và nhận phản hồi
            response = chat.send_message(last_msg["content"])
            return response.text
        except Exception as e:
            logger.error(f"Error generating chat response from Gemini API: {str(e)}")
            return f"Sorry, I encountered an error: {str(e)}"
    
    def generate_multimodal_response(self, prompt: str, image_data: Union[str, bytes], 
                                    context: Optional[str] = None) -> str:
        """
        Generate a response based on both text and image
        
        Args:
            prompt (str): The user's text prompt
            image_data (Union[str, bytes]): Image data or URL
            context (Optional[str]): Additional context
            
        Returns:
            str: The generated response
        """
        try:
            # Chuẩn bị dữ liệu đầu vào
            parts = []
            
            # Thêm ảnh vào parts
            if isinstance(image_data, str) and (image_data.startswith('http://') or image_data.startswith('https://')):
                # Nếu là URL
                image_part = {"image_url": image_data}
                parts.append(image_part)
            else:
                # Nếu là dữ liệu nhị phân
                parts.append({"image": image_data})
            
            # Thêm context nếu có
            if context:
                full_prompt = f"{context}\n\n{prompt}"
            else:
                full_prompt = prompt
                
            # Thêm prompt của người dùng
            parts.append(full_prompt)
            
            # Tạo nội dung
            response = self.model.generate_content(parts)
            return response.text
        except Exception as e:
            logger.error(f"Error generating multimodal response from Gemini API: {str(e)}")
            return f"Sorry, I encountered an error processing your image: {str(e)}"