"""
簡易追跡システム
IOUベースのID継承機能
"""

from typing import List, Dict, Tuple, Optional
from .iou_calculator import calculate_iou


class SimpleTracker:
    """簡易IOUトラッカー"""
    
    def __init__(self, iou_threshold: float = 0.5):
        """
        初期化
        
        Args:
            iou_threshold: マッチング判定のIOU閾値
        """
        self.iou_threshold = iou_threshold
        
    def find_best_match(self, target_bb: Dict, candidate_bbs: List[Dict]) -> Tuple[Optional[Dict], float]:
        """
        ターゲットBBに最もマッチする候補BBを見つける
        
        Args:
            target_bb: マッチング対象のBB
            candidate_bbs: 候補BBリスト
            
        Returns:
            Tuple[Optional[Dict], float]: (最適マッチBB, IOU値)
        """
        best_match = None
        best_iou = 0.0
        
        for candidate in candidate_bbs:
            iou = calculate_iou(target_bb, candidate)
            if iou > best_iou and iou >= self.iou_threshold:
                best_iou = iou
                best_match = candidate
                
        return best_match, best_iou
        
    def track_bb_with_id_inheritance(self, new_bb: Dict, previous_bbs: List[Dict]) -> Tuple[Dict, bool, float]:
        """
        新しいBBに対してID継承を試みる
        
        Args:
            new_bb: 新しいBB（IDなし）
            previous_bbs: 前フレームのBBリスト
            
        Returns:
            Tuple[Dict, bool, float]: (ID設定済みBB, ID継承フラグ, IOU値)
        """
        # 最適マッチを探す
        best_match, best_iou = self.find_best_match(new_bb, previous_bbs)
        
        if best_match:
            # ID継承
            tracked_bb = new_bb.copy()
            tracked_bb['individual_id'] = best_match['individual_id']
            tracked_bb['inherited'] = True
            tracked_bb['source_bb_id'] = best_match.get('id', 'unknown')
            tracked_bb['tracking_iou'] = best_iou
            return tracked_bb, True, best_iou
        else:
            # 新規ID（継承なし）
            return new_bb, False, 0.0
            
    def batch_track_with_id_inheritance(self, new_bbs: List[Dict], 
                                       previous_bbs: List[Dict]) -> List[Tuple[Dict, bool, float]]:
        """
        複数のBBに対して一括でID継承を試みる
        
        Args:
            new_bbs: 新しいBBリスト
            previous_bbs: 前フレームのBBリスト
            
        Returns:
            List[Tuple[Dict, bool, float]]: [(ID設定済みBB, ID継承フラグ, IOU値), ...]
        """
        results = []
        used_previous_bbs = set()
        
        # 貪欲法でマッチング
        for new_bb in new_bbs:
            # 使用済みでない前フレームBBから候補を選択
            available_previous = [bb for i, bb in enumerate(previous_bbs) 
                                if i not in used_previous_bbs]
            
            if available_previous:
                best_match, best_iou = self.find_best_match(new_bb, available_previous)
                
                if best_match:
                    # マッチしたBBのインデックスを記録
                    for i, bb in enumerate(previous_bbs):
                        if bb is best_match:
                            used_previous_bbs.add(i)
                            break
                    
                    # ID継承
                    tracked_bb = new_bb.copy()
                    tracked_bb['individual_id'] = best_match['individual_id']
                    tracked_bb['inherited'] = True
                    tracked_bb['source_bb_id'] = best_match.get('id', 'unknown')
                    tracked_bb['tracking_iou'] = best_iou
                    results.append((tracked_bb, True, best_iou))
                else:
                    results.append((new_bb, False, 0.0))
            else:
                results.append((new_bb, False, 0.0))
                
        return results