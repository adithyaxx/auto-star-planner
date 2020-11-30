# first, check if courseInfo is set (default: False)
# courseInfo will contain courseType and lecture(s), if any
# if courseInfo is set, gather the rest of the index data

# if not set, gather courseInfo as well as index data
# if remarks == Online Course, type = 4
# if gotLec, means course is 1 or 2. need to verify in the next index 
# (if gotLec && gotLab is set, type = 1. elif gotLec && !gotLab, type = 2)
# (else, type = 3)

# i need 2x [31*6] list (0800-0830 - 2300-2330) * (Mon - Sat)
from enum import Enum

class typeInfoEnum(Enum):
    LEC = 1
    TUT = 2
    LAB = 3

class courseType(Enum):
    LECTUTLAB = 1
    LECTUT = 2
    TUT = 3
    ONLINE = 4

class Lecture:
    def __init__(self, day, time):
        self.day = day
        self.time = time

    def getLecTiming(self):
        return f"{self.day}, {self.time}"

class IndexInfo:
    def __init__(self, day, time, indexInfoType):
        self.day = day
        self.time = time
        self.indexInfoType = indexInfoType

    def getTiming(self):
        if self.indexInfoType == typeInfoEnum.TUT:
            return f"Tutorial, {self.day}, {self.time}"
        else:
            return f"Lab, {self.day}, {self.time}, {self.remarks} week"

class Index:
    def __init__(self, indexNo):
        self.indexNo = indexNo
        self.indexInfoList = []

class Course:
    def __init__(self, courseCode):
        self.courseCode = courseCode
        self.indexList = []
        self.lecList = []

    def getLecTiming(self):
        if not self.lecList:    # list is empty
            print("This course has no lecture")
        else:
            for lec in self.lecList:
                print(f"\t{lec.getLecTiming()}")

    def printCourseInfo(self):
        print(f"Course Code: {self.courseCode}")
        self.getLecTiming()
        for index in self.indexList:
            print(f"\tIndex: {index.indexNo}")
            for indexInfo in index.indexInfoList:
                print(f"\t\t{indexInfo.getTiming()}") 