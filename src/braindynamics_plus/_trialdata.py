import bisect

# CONSTANTS
MARK_TIME_IDX = 0 # index of timestamp in tuple representing trial event
MARK_CODE_IDX = 1 # index of the event code
MARK_INVALID_TYPE = -1 # invalid type

class _TrialData:
    def __init__(self):
        self.start_time = MARK_INVALID_TYPE
        self.end_time = MARK_INVALID_TYPE
        self.mark_list = list()

    def __str__(self)->str:
        return f"Trial start: {self.start_time}; end: {self.end_time}. Trial markers: {self.mark_list}"

    def _update_begin_end(self) -> None:
        if len(self.mark_list) == 0:
            self.clear()
        else:
            self.start_time = self.mark_list[0][MARK_TIME_IDX]
            self.end_time = self.mark_list[-1][MARK_TIME_IDX] + 1

    def duration(self) -> int:
        return self.end_time - self.start_time
    
    def empty(self) -> bool:
        return self.duration() == 0
    
    def mark_count(self) -> int:
        return len(self.mark_list)
    
    def clear(self) -> None:
        self.start_time = self.end_time = MARK_INVALID_TYPE
        self.mark_list.clear()

    def append_mark(self, mark : tuple) -> None:
        if self.empty():
            self.start_time = mark[MARK_TIME_IDX]
            self.end_time = self.start_time + 1
            self.mark_list.append(mark)
        else:
            if(mark[MARK_TIME_IDX] < self.end_time - 1):
                raise ValueError("Invalid mark time")
            else:
                if self.mark_list[-1] != mark:
                    self.end_time = mark[MARK_TIME_IDX] + 1
                    self.mark_list.append(mark)

    def insert_mark(self, mark : tuple) -> None:
        if self.empty():
            self.append_mark(mark)
            return

        insert_idx = bisect.bisect_left(self.mark_list, mark)
        if insert_idx >= len(self.mark_list):
            self.mark_list.insert(insert_idx, mark)
        else:
            if (self.mark_list[insert_idx] != mark):
                self.mark_list.insert(insert_idx, mark)
        self.start_time = min(self.start_time, mark[MARK_TIME_IDX])
        self.end_time = max(self.end_time, mark[MARK_TIME_IDX])

    def erase_mark(self, mark : tuple) -> int:
        erased_count = 0
        found_idx = [i for i, m in enumerate(self.mark_list) if m == mark]
        erased_count = len(found_idx)
        for i in reversed(found_idx):
            del self.mark_list[i]
        self._update_begin_end()
        return erased_count