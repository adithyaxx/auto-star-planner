from bs4 import BeautifulSoup
import os
from courses import (Course, Index, courseType, typeInfoEnum, Lecture, IndexInfo)

import sys
import window
import addCourses

from PyQt5.QtCore import (pyqtSignal, pyqtSlot)
from PyQt5.QtGui import (QFont, QTextCharFormat)
from PyQt5.QtWidgets import (QApplication, QMainWindow, QDialog, QMessageBox, QLabel)

class AddCourses(QDialog, addCourses.Ui_dialog):
    lecInfo = pyqtSignal(int, list, str)
    
    def __init__(self):
        super(AddCourses, self).__init__()
        self.courseList = []
        self.selectedCourse = []
        self.colDict = {
            "MON":0,
            "TUE":1,
            "WED":2,
            "THU":3,
            "FRI":4,
            "SAT":5,
        }
        self.dayTimeRowDict = {
            "0800":0,
            "0830":1,
            "0900":2,
            "0930":3,
            "1000":4,
            "1030":5,
            "1100":6,
            "1130":7,
            "1200":8,
            "1230":9,
            "1300":10,
            "1330":11,
            "1400":12,
            "1430":13,
            "1500":14,
            "1530":15,
            "1600":16,
            "1630":17,
            "1700":18,
            "1730":19,
            "1800":20,
            "1830":21,
            "1900":22,
            "1930":23,
            "2000":24,
            "2030":25,
            "2100":26,
            "2130":27,
            "2200":28,
            "2230":29,
            "2300":30,
        }

        self.dayTime = []
        self.dayTimeEvenOdd = []
        for i in range(0, 31):
            self.dayTime.append([0] * 6)
            self.dayTimeEvenOdd.append(["NIL"] * 6)     # NIL, A = All week, E = Even week, O = Odd Week, EO = Even and Odd Week

        self.setupUi(self)
        self.planBtn.pressed.connect(self.check)

    def check(self):
        if self.planBtn.text() == "Check":
            self.selectedCourse.clear()
            addCourseList = self.coursesTxtEdit.toPlainText().upper().split()
            for course in addCourseList:
                valid = False
                if not valid:
                    for course2 in self.courseList:
                        if course == course2.courseCode:
                            self.selectedCourse.append(course2)
                            valid = True
                            break
                if not valid:
                    culprit = course
                    break
            
            if not valid:
                QMessageBox.critical(self, "Add Course", f"{culprit} is not found in class schedule")
            else:
                self.planBtn.setText("Plan")
                QMessageBox.information(self, "Add Course", "Check OK!\nPress the plan button")
        else:
            self.plan()

    def plan(self):
        print("Plan my semester...")
        # Step 1: Check for clashing lectures (Future update: Check which course lecture clash with which)
        if not (self.setLecTimeOnArray()):
            QMessageBox.critical(self, "Add Course", "Unable to plan the semester with these course setup.\nThere are clashing lectures.")
            return False

        # Step 2: Remove all the course indexes that clashes with the set course lecture
        if not (self.removeClashingCourseIndexes()):
            QMessageBox.critical(self, "Add Course", "Unable to plan the semester with these course setup.\nThere's a course with 0 index after removing index clashing with lectures")
            return False

        # Step 3: Create index graph
        self.createIndexGraph()
        # for course in self.selectedCourse:
        #     print(f"{course.courseCode}")
        #     for index in course.indexList:
        #         print(f"\tIndex: {index.indexNo}")
        #         if index.next:
        #             for nextIndex in index.next:
        #                 print(f"\t\tNext Index: {nextIndex.indexNo}")
        
        # Step 4: Do DFS, removing all the clashing links
        self.dfsRemoveLink()

    def createIndexGraph(self):
        for i in range(len(self.selectedCourse) - 1):
           for index in self.selectedCourse[i].indexList:
               index.next = self.selectedCourse[i+1].indexList.copy()     

    # it works... partially... i didnt take care of lab. got even/odd week. can cramp 2 different indexes lab into 1 timing
    def dfsRemoveLink(self):
        for index in self.selectedCourse[0].indexList:
            self.tempMarkDayTime(index)
            self.dfs(index)
            self.unmarkDayTime(index)

    def dfs(self, index):
        if index.next:
            tempIndexList = []
            for nextIndex in index.next:
                for nextIndexInfo in nextIndex.indexInfoList:
                    if nextIndexInfo.indexInfoType == typeInfoEnum.TUT:
                        if (self.gotClash(self.getColIndex(nextIndexInfo.day), self.getRowRangeIndex(nextIndexInfo.time))):
                            tempIndexList.append(nextIndex)
                            break
                    else:   # If not tut, there can only be lab. but idk. i could be wrong. will update later in the future maybe
                        if (self.gotClashForLab(self.getColIndex(nextIndexInfo.day), self.getRowRangeIndex(nextIndexInfo.time), nextIndexInfo.remarks)):
                            tempIndexList.append(nextIndex)
                            break
            # remove the clashing index from nextIndex
            for tempIndex in tempIndexList:
                index.next.remove(tempIndex)
            # check if there's at least 1 index in index.next
            if index.next:
                for nextIndex in index.next:
                    self.tempMarkDayTime(nextIndex)
                    self.dfs(nextIndex)
                    self.unmarkDayTime(nextIndex)

    def tempMarkDayTime(self, index):
        for indexInfo in index.indexInfoList:
            if indexInfo.indexInfoType == typeInfoEnum.TUT:
                self.setOnArray(self.getColIndex(indexInfo.day), self.getRowRangeIndex(indexInfo.time))
            else:
                self.setOnArrayForLab(self.getColIndex(indexInfo.day), self.getRowRangeIndex(indexInfo.time), indexInfo.remarks)
    
    def unmarkDayTime(self, index):
        for indexInfo in index.indexInfoList:
            if indexInfo.indexInfoType == typeInfoEnum.TUT:
                self.unsetArray(self.getColIndex(indexInfo.day), self.getRowRangeIndex(indexInfo.time))
            else:
                self.unsetArrayForLab(self.getColIndex(indexInfo.day), self.getRowRangeIndex(indexInfo.time), indexInfo.remarks)

    def unsetArray(self, col, rowRange):
        for row in range(rowRange[0], rowRange[1]):
            self.dayTime[row][col] = 0
            self.dayTimeEvenOdd[row][col] = "NIL"

    def getColIndex(self, day):
        return self.colDict.get(day)

    def getRowRangeIndex(self, time):
        timeList = time.split("-")
        startEnd = [self.dayTimeRowDict.get(timeList[0]), self.dayTimeRowDict.get(timeList[1])]
        return startEnd

    def setOnArray(self, col, rowRange):
        ableToSet = True
        for row in range(rowRange[0], rowRange[1]):
            if self.dayTime[row][col] == 0:
                self.dayTime[row][col] = 1
                self.dayTimeEvenOdd[row][col] = "A"
            else:
                ableToSet = False
                break
        return ableToSet

    def unsetArrayForLab(self, col, rowRange, remarks):
        for row in range(rowRange[0], rowRange[1]):
            if (remarks == "Even" and self.dayTimeEvenOdd[row][col] == "EO"):
                self.dayTimeEvenOdd[row][col] = "O"
            elif (remarks == "Odd" and self.dayTimeEvenOdd[row][col] == "EO"):
                self.dayTimeEvenOdd[row][col] = "E"
            else:
                self.dayTimeEvenOdd[row][col] = "NIL"
                self.dayTime[row][col] = 0

    def setOnArrayForLab(self, col, rowRange, remarks):
        ableToSet = True
        for row in range(rowRange[0], rowRange[1]):
            if self.dayTime[row][col] == 0:
                self.dayTime[row][col] = 1
                if remarks == "Even":
                    self.dayTimeEvenOdd[row][col] = "E"
                else:
                    self.dayTimeEvenOdd[row][col] = "O"
            else:   # something is occupying that slot. need to check
                if self.dayTimeEvenOdd[row][col] == "A":
                    ableToSet = False
                    break
                elif (remarks == "Even" and self.dayTimeEvenOdd[row][col] == "O") or (remarks == "Odd" and self.dayTimeEvenOdd[row][col] == "E"):
                    self.dayTimeEvenOdd[row][col] = "EO"
                else:
                    ableToSet = False
                    break
        return ableToSet

    # translate the time {MON, 0800 - 0830} to dayTime[][]
    def setLecTimeOnArray(self):
        for course in self.selectedCourse:
            for lecTiming in course.getLecTiming():
                if not (self.setOnArray(self.getColIndex(lecTiming[0]), self.getRowRangeIndex(lecTiming[1]))):
                    return False
        return True
        # Do this code at the end after got valid plan(s)
        # for course in self.selectedCourse:
        #     for lecTiming in course.getLecTiming():
        #         self.lecInfo.emit(self.getColIndex(lecTiming[0]), self.getRowRangeIndex(lecTiming[1]), f"{course.courseCode} Lec")

    # removing course indexes that clashes with lecture timing
    def removeClashingCourseIndexes(self):
        for course in self.selectedCourse:
            tempIndexList = []
            for index in course.indexList:  # a course may have multiple indexes. indexes are like different classes
                for indexInfo in index.indexInfoList:   # an index may have tutorial and lab. those are indexInfo
                    if (self.gotClash(self.getColIndex(indexInfo.getTiming()[0]), self.getRowRangeIndex(indexInfo.getTiming()[1]))):
                        tempIndexList.append(index)
                        break
            # remove the clashing index from the course
            for tempIndex in tempIndexList:
                course.indexList.remove(tempIndex)
            # check the current indexList size
            if len(course.indexList) == 0:
                return False
        return True               

    def gotClashForLab(self, col, rowRange, remarks):
        for row in range(rowRange[0], rowRange[1]):
            if remarks == "Even" and (self.dayTimeEvenOdd[row][col] == "A" or self.dayTimeEvenOdd[row][col] == "E" or self.dayTimeEvenOdd[row][col] == "EO"):
                return True
            elif remarks == "Odd" and (self.dayTimeEvenOdd[row][col] == "A" or self.dayTimeEvenOdd[row][col] == "O" or self.dayTimeEvenOdd[row][col] == "EO"):
                return True
        return False

    def gotClash(self, col, rowRange):
        for row in range(rowRange[0], rowRange[1]):
            if self.dayTime[row][col] == 1:
                return True
        return False

class Window(QMainWindow, window.Ui_MainWindow):
    def __init__(self):
        super(Window, self).__init__()
        self.courseList = []

        self.setupUi(self)
        self.loaded = False
        self.addCoursesDialog = AddCourses()
        self.addCoursesDialog.lecInfo.connect(self.on_lecInfo_emitted)

        self.actionLoad_Class_Schedule.triggered.connect(self.loadClassSchedule)
        self.actionAdd_Courses.triggered.connect(self.openAddCoursesDialog)

    @pyqtSlot(int, list, str)
    def on_lecInfo_emitted(self, col, rowRange, info):
        for row in range(rowRange[0], rowRange[1]):
            self.plannerTable.setCellWidget(row, col, QLabel(info))

    def duplCourse(self, name):
        for course in self.courseList:
            if name == course.courseCode:
                return True
        return False

    def retrieveCourses(self, soup):
        i = 0
        dupl = False
        for table in soup("table"):
            if i % 2 == 0:
                if not self.duplCourse("".join(table.font.findAll(text=True))):
                    self.courseList.append(Course("".join(table.font.findAll(text=True))))
                else:
                    dupl = True
            if i % 2 == 1:
                if not dupl:
                    self.retrieveIndexes(table, self.courseList[-1])
                else:
                    dupl = False
            i += 1

    def retrieveIndexes(self, table, course):
        courseInfoSet = gotLec = gotLab = False
        first = True
        col = 0 # the table only has 7 columns
        typeInfo = None
        
        for item in table("td"):
            if col % 7 == 0:  # Index
                indexNo = "".join(item.findAll(text=True))
                if indexNo:   # if indexNo is not empty
                    if first:
                        first = False
                        index = Index(indexNo)
                    else:   # this is the second index onwards
                        course.indexList.append(index)
                        index = Index(indexNo)
                        if not courseInfoSet:
                            if gotLec and gotLab:
                                course.type = courseType.LECTUTLAB
                            elif gotLec and not gotLab:
                                course.type = courseType.LECTUT
                            else:
                                course.type = courseType.TUT
                            courseInfoSet = True
            if col % 7 == 1:  # Type: (blank(for online courses), LEC/STUDIO, TUT, LAB)
                if "".join(item.findAll(text=True)) == "LEC/STUDIO":
                    gotLec = True
                    typeInfo = typeInfoEnum.LEC
                elif "".join(item.findAll(text=True)) == "TUT":
                    typeInfo = typeInfoEnum.TUT
                elif "".join(item.findAll(text=True)) == "LAB":
                    gotLab = True
                    typeInfo = typeInfoEnum.LAB
            if col % 7 == 3:  # Day: (MON, TUE, WED, THU, FRI)
                day = "".join(item.findAll(text=True))
            if col % 7 == 4:  # Time
                time = "".join(item.findAll(text=True))
                if typeInfo:
                    if typeInfo == typeInfoEnum.LEC and not courseInfoSet:
                        course.lecList.append(Lecture(day, time))
                    elif typeInfo == typeInfoEnum.TUT:
                        index.indexInfoList.append(IndexInfo(day, time, typeInfoEnum.TUT))
            if col % 7 == 6:  # Remarks: (blank, Teaching Wk(tut and lab got its own teaching week), Online Course)
                if "".join(item.findAll(text=True)) == "Online Course":
                    courseInfoSet = True
                    course.type = courseType.ONLINE
                elif "".join(item.findAll(text=True)) == "Teaching Wk2,4,6,8,10,12":
                    index.indexInfoList.append(IndexInfo(day, time, typeInfoEnum.LAB))
                    index.indexInfoList[-1].remarks = "Even"
                elif "".join(item.findAll(text=True)) == "Teaching Wk1,3,5,7,9,11,13":
                    index.indexInfoList.append(IndexInfo(day, time, typeInfoEnum.LAB))
                    index.indexInfoList[-1].remarks = "Odd"
            col += 1
        course.indexList.append(index)  # this is to add the last index as the algo only add the index at the next index

    def loadClassSchedule(self):
        self.loaded = True
        self.courseList.clear
        for fileName in os.listdir("classSchedule"):
            with open(os.path.join("classSchedule", fileName), 'r') as f:
                content = f.read()
                soup = BeautifulSoup(content, "html.parser")
                self.retrieveCourses(soup)
        self.addCoursesDialog.courseList = self.courseList
        self.actionLoad_Class_Schedule.setText("Reload Class Schedule")
        QMessageBox.information(self, "Load Class Schedule", f"{len(self.courseList)} class schedules loaded.")

    def openAddCoursesDialog(self):
        if not self.loaded:
            QMessageBox.critical(self, "Add Course", "Please load the class schedule first")
        else:
            self.addCoursesDialog.show()

def main():
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()