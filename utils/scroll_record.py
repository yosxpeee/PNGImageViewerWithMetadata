def record_left_scroll_position(page, current_path_text, scroll_pos):
    if scroll_pos["t"] == "end":
        tmp_info = {current_path_text.value: {"scroll_pos": scroll_pos["p"], "window_height": page.window.height}}
        overwritten = False
        for index, item in enumerate(page.scroll_position_history_left):
            if current_path_text.value in item:
                if scroll_pos["p"] > 0:
                    page.scroll_position_history_left[index] = tmp_info
                else:
                    page.scroll_position_history_left.pop(index)
                overwritten = True
                break
        if not overwritten and scroll_pos["p"] > 0:
            page.scroll_position_history_left.append(tmp_info)


def record_center_scroll_position(page, current_path_text, scroll_pos):
    if scroll_pos["t"] == "end":
        tmp_info = {current_path_text.value: {"scroll_pos": scroll_pos["p"], "window_height": page.window.height}}
        overwritten = False
        for index, item in enumerate(page.scroll_position_history_center):
            if current_path_text.value in item:
                if scroll_pos["p"] > 0:
                    page.scroll_position_history_center[index] = tmp_info
                else:
                    page.scroll_position_history_center.pop(index)
                overwritten = True
                break
        if not overwritten and scroll_pos["p"] > 0:
            page.scroll_position_history_center.append(tmp_info)


def replay_left_scroll_position(page, current_path_text, dir_list):
    for index, item in enumerate(page.scroll_position_history_left):
        if current_path_text.value in item:
            info = page.scroll_position_history_left[index]
            if page.window.height == info[current_path_text.value]["window_height"]:
                dir_list.scroll_to(info[current_path_text.value]["scroll_pos"])
                page.update()
            else:
                page.scroll_position_history_left.pop(index)


def replay_center_scroll_position(page, current_path_text, thumbnail_grid):
    for index, item in enumerate(page.scroll_position_history_center):
        if current_path_text.value in item:
            info = page.scroll_position_history_center[index]
            if page.window.height == info[current_path_text.value]["window_height"]:
                thumbnail_grid.scroll_to(info[current_path_text.value]["scroll_pos"])
                page.update()
            else:
                page.scroll_position_history_center.pop(index)