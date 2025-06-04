"""
MessageSerializer - メッセージシリアライズ
高速なメッセージのシリアライズ/デシリアライズ
"""
import json
import pickle
import time
import uuid
from dataclasses import dataclass, asdict
from typing import Any, Dict, Union, Optional
import logging


@dataclass
class Message:
    """標準メッセージ形式"""
    id: str
    source: str
    target: str
    type: str
    data: Dict[str, Any]
    timestamp: float
    priority: str = "normal"  # high, normal, low
    timeout: Optional[int] = None  # ms
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.timestamp:
            self.timestamp = time.perf_counter()


class MessageSerializer:
    """
    高速メッセージシリアライズ
    JSON（軽量）とPickle（高速）の使い分け
    """
    
    def __init__(self, use_json: bool = True):
        self.use_json = use_json
        self._logger = logging.getLogger(__name__)
    
    def serialize_message(self, message: Message) -> bytes:
        """
        メッセージシリアライズ
        
        Args:
            message: Message オブジェクト
            
        Returns:
            bytes: シリアライズされたデータ
        """
        try:
            if self.use_json:
                return self._serialize_json(message)
            else:
                return self._serialize_pickle(message)
                
        except Exception as e:
            self._logger.error(f"Message serialization failed: {e}")
            raise
    
    def deserialize_message(self, data: bytes) -> Message:
        """
        メッセージデシリアライズ
        
        Args:
            data: シリアライズされたデータ
            
        Returns:
            Message: デシリアライズされたMessage
        """
        try:
            if self.use_json:
                return self._deserialize_json(data)
            else:
                return self._deserialize_pickle(data)
                
        except Exception as e:
            self._logger.error(f"Message deserialization failed: {e}")
            raise
    
    def serialize_data(self, data: Any) -> bytes:
        """任意データのシリアライズ"""
        try:
            if self.use_json:
                return json.dumps(data, ensure_ascii=False).encode('utf-8')
            else:
                return pickle.dumps(data, protocol=pickle.HIGHEST_PROTOCOL)
        except Exception as e:
            self._logger.error(f"Data serialization failed: {e}")
            raise
    
    def deserialize_data(self, data: bytes, data_type: type = dict) -> Any:
        """任意データのデシリアライズ"""
        try:
            if self.use_json:
                return json.loads(data.decode('utf-8'))
            else:
                return pickle.loads(data)
        except Exception as e:
            self._logger.error(f"Data deserialization failed: {e}")
            raise
    
    def _serialize_json(self, message: Message) -> bytes:
        """JSON形式でシリアライズ"""
        message_dict = asdict(message)
        return json.dumps(message_dict, ensure_ascii=False).encode('utf-8')
    
    def _deserialize_json(self, data: bytes) -> Message:
        """JSON形式からデシリアライズ"""
        message_dict = json.loads(data.decode('utf-8'))
        return Message(**message_dict)
    
    def _serialize_pickle(self, message: Message) -> bytes:
        """Pickle形式でシリアライズ"""
        return pickle.dumps(message, protocol=pickle.HIGHEST_PROTOCOL)
    
    def _deserialize_pickle(self, data: bytes) -> Message:
        """Pickle形式からデシリアライズ"""
        return pickle.loads(data)
    
    def estimate_size(self, message: Message) -> int:
        """メッセージサイズ推定"""
        try:
            serialized = self.serialize_message(message)
            return len(serialized)
        except Exception:
            return 0


def create_message(source: str, target: str, message_type: str, 
                  data: Dict[str, Any], priority: str = "normal",
                  timeout: Optional[int] = None) -> Message:
    """メッセージ作成ヘルパー"""
    return Message(
        id=str(uuid.uuid4()),
        source=source,
        target=target,
        type=message_type,
        data=data,
        timestamp=time.perf_counter(),
        priority=priority,
        timeout=timeout
    )


def create_request_message(source: str, target: str, service_name: str,
                          params: Dict[str, Any], timeout: int = 1000) -> Message:
    """リクエストメッセージ作成"""
    return create_message(
        source=source,
        target=target,
        message_type="request",
        data={
            "service": service_name,
            "params": params
        },
        priority="normal",
        timeout=timeout
    )


def create_response_message(request_message: Message, result: Any, 
                           success: bool = True, error: str = "") -> Message:
    """レスポンスメッセージ作成"""
    return create_message(
        source=request_message.target,
        target=request_message.source,
        message_type="response",
        data={
            "request_id": request_message.id,
            "result": result,
            "success": success,
            "error": error
        },
        priority=request_message.priority
    )