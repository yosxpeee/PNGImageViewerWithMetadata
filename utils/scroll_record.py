########################################
# scroll_record.py
#
# スクロール位置関連(人力でコード分割)
########################################
import flet as ft

####################
# ファイルブラウザのスクロール位置記録
####################
def record_left_scroll_position(
        page: ft.Page, 
        current_path_text: ft.Text, 
        scroll_pos: dict
    ):
    if scroll_pos["t"] == "end":
        tmpInfo = {current_path_text.value:{"scroll_pos":scroll_pos["p"], "window_height":page.window.height}}
        #print("tmpInfo:"+str(tmpInfo))
        overwrited = False
        for index, item in enumerate(page.scroll_position_history_left):
            if current_path_text.value in item:
                if scroll_pos["p"] > 0:
                    page.scroll_position_history_left[index] = tmpInfo
                    #print("同じ場所記録済みかつPOS:0以上なのでなので上書き")
                else:
                    page.scroll_position_history_left.pop(index)
                    #print("同じ場所記録済みかつPOS:0なので履歴を削除")
                overwrited = True #消してもTrueにする
                break
        if overwrited == False:
            if scroll_pos["p"] > 0:
                page.scroll_position_history_left.append(tmpInfo)
                #print("同じ場所がないかつPOS:0以上なので追加")
        #print(page.scroll_position_history_left)

####################
# サムネイルグリッドのスクロール位置記録
####################
def record_center_scroll_position(
        page: ft.Page, 
        current_path_text: ft.Text,
        scroll_pos: dict
    ):
    if scroll_pos["t"] == "end":
            tmpInfo = {current_path_text.value:{"scroll_pos":scroll_pos["p"], "window_height":page.window.height}}
            #print("tmpInfo:"+str(tmpInfo))
            overwrited = False
            for index, item in enumerate(page.scroll_position_history_center):
                if current_path_text.value in item:
                    if scroll_pos["p"] > 0:
                        page.scroll_position_history_center[index] = tmpInfo
                        #print("同じ場所記録済みかつPOS:0以上なのでなので上書き")
                    else:
                        page.scroll_position_history_center.pop(index)
                        #print("同じ場所記録済みかつPOS:0なので履歴を削除")
                    overwrited = True #消してもTrueにする
                    break
            if overwrited == False:
                if scroll_pos["p"] > 0:
                    page.scroll_position_history_center.append(tmpInfo)
                    #print("同じ場所がないかつPOS:0以上なので追加")

####################
# ファイルブラウザのスクロール位置復元
####################
def replay_left_scroll_position(
        page: ft.Page, 
        current_path_text: ft.Text,
        dir_list: ft.ListView,
    ):
    for index, item in enumerate(page.scroll_position_history_left):
        if current_path_text.value in item:
            #print("見つかりました："+str(page.scroll_position_history_left[index]))
            info = page.scroll_position_history_left[index]
            if page.window.height == info[current_path_text.value]["window_height"]:
                # 高さが同じなら復元する
                dir_list.scroll_to(info[current_path_text.value]["scroll_pos"])
                page.update()
            else:
                # 高さが違うなら復元せず履歴削除(復元しない＝POS:0なので履歴不要)
                page.scroll_position_history_left.pop(index)

####################
# サムネイルグリッドのスクロール位置復元
####################
def replay_center_scroll_position(
        page: ft.Page, 
        current_path_text: ft.Text,
        thumbnail_grid: ft.GridView,
    ):
    for index, item in enumerate(page.scroll_position_history_center):
        if current_path_text.value in item:
            #print("見つかりました："+str(page.scroll_position_history_center[index]))
            info = page.scroll_position_history_center[index]
            if page.window.height == info[current_path_text.value]["window_height"]:
                # 高さが同じなら復元する
                thumbnail_grid.scroll_to(info[current_path_text.value]["scroll_pos"])
                page.update()
            else:
                # 高さが違うなら復元せず履歴削除(復元しない＝POS:0なので履歴不要)
                page.scroll_position_history_center.pop(index)