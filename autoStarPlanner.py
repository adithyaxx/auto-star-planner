from bs4 import BeautifulSoup
import os
from courses import (Course, Index, courseType, typeInfoEnum, Lecture, IndexInfo)

import sys
import window
import addCourses
from PyQt5.QtGui import (QFont, QTextCharFormat)
from PyQt5.QtWidgets import (QApplication, QMainWindow, QDialog, QMessageBox)

class AddCourses(QDialog, addCourses.Ui_dialog):
    def __init__(self):
        super(AddCourses, self).__init__()
        self.courseList = []
        
        temp = [0] * 6
        self.startDayTime = []
        self.endDayTime = []
        for i in range(0, 31):
            self.startDayTime.append(temp)
            self.endDayTime.append(temp)
        
        self.setupUi(self)
        self.planBtn.pressed.connect(self.check)

    def check(self):
        if self.planBtn.text() == "Check":
            addCourseList = self.coursesTxtEdit.toPlainText().upper().split()
            for course in addCourseList:
                valid = False
                if not valid:
                    for course2 in self.courseList:
                        if course == course2.courseCode:
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
        # step 1: set all the lecture timing
        # lecture timing is impt. if got clash, automatically means the program is 
        # unable to plan the semester using the current added courses

        # step 2: get the course with the smallest index size from the added courses
        # this course is the priority. if not plan this course, auto reject

        # step 3: loop step 2 with the next smallest index using recursion? 
        # constraint: my 2 arrays defined in init, need to dynamically set and remove.
        # if unable to add index, go to next index
        # if unable to add all index, auto reject
        # if able get n index planned, signal and slot to main comboBox(need to figure out)
        # maybe using list

        # additional function(s) to implement:
        # an index start-end time to its proper startDayTime and endDayTime indexes


class Window(QMainWindow, window.Ui_MainWindow):
    def __init__(self):
        super(Window, self).__init__()
        self.courseList = []

        self.setupUi(self)
        self.loaded = False
        self.addCoursesDialog = AddCourses()
        self.actionLoad_Class_Schedule.triggered.connect(self.loadClassSchedule)
        self.actionAdd_Courses.triggered.connect(self.openAddCoursesDialog)

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
        for fileName in os.listdir("classSchedule"):
            with open(os.path.join("classSchedule", fileName), 'r') as f:
                content = f.read()
                soup = BeautifulSoup(content, "html.parser")
                self.retrieveCourses(soup)
        self.addCoursesDialog.courseList = self.courseList
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