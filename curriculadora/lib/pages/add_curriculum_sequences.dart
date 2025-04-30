import 'package:curriculadora/models/reading-test.dart';
import 'package:flutter/material.dart';

class AddCurriculumSequences extends StatefulWidget {
  final int page;
  final Map<String, dynamic> formDataCurriculum;
  final Map<String, dynamic> formDataCourses;
  final Function(int newPage) changePage;
  const AddCurriculumSequences(
      {super.key,
      required this.page,
      required this.formDataCurriculum,
      required this.formDataCourses,
      required this.changePage});

  @override
  State<AddCurriculumSequences> createState() => _AddCurriculumSequencesState();
}

class _AddCurriculumSequencesState extends State<AddCurriculumSequences> {
  late int currentSequence;
  late int totalSequences;
  late List<Map<String, dynamic>> sequenceList;

  @override
  void initState() {
    super.initState();
    currentSequence = 0;
    sequenceList = getRecommendations();
    totalSequences = sequenceList.length;
  }

  List<Map<String, dynamic>> getRecommendations() {
    // Map<String, dynamic> recs = testRecommendations();
    return testRecommendations()["recommendations"];
  }

  Widget displayRow(String courseCode, int requisites, int requisitesFor) {
    return Row(
      children: [
        Text(courseCode),
        const Spacer(),
        RichText(
            text: TextSpan(children: [
          const WidgetSpan(child: Icon(Icons.lock)),
          TextSpan(text: requisites.toString()),
          const WidgetSpan(child: Icon(Icons.key)),
          TextSpan(text: requisitesFor.toString())
        ])),
      ],
    );
  }

  Widget displaySemester(List<Widget> child) {
    return Container(
        decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(5),
            color: Colors.white,
            boxShadow: const [
              BoxShadow(
                  blurRadius: 1, offset: Offset(1, 1), color: Colors.black12)
            ]),
        width: MediaQuery.sizeOf(context).width - 30,
        child: Padding(
            padding: const EdgeInsets.all(10),
            child: Column(
              children: child,
            )));
  }

  List<Widget> displaySequence(Map<String, dynamic> sequence) {
    List<Map<String, dynamic>> details = sequence["schedule_details"];
    List<Widget> semesterList = [];
    for (int i = 0; i < details.length; i++) {
      List<Widget> courseList = [];
      courseList.add(Row(
        children: [
          Text(details[i]["term_name"],
              style: TextStyle(color: Colors.black.withValues(alpha: 0.5))),
        ],
      ));
      courseList.add(
        const SizedBox(
          height: 5,
        ),
      );
      List<String> courses = details[i]["courses"];
      for (int j = 0; j < courses.length; j++) {
        courseList.add(displayRow(courses[j], 0, 0));
        courseList.add(const Divider());
      }
      courseList.removeLast();
      semesterList.add(displaySemester(courseList));
      semesterList.add(
        const SizedBox(
          height: 10,
        ),
      );
    }
    return semesterList;
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        // Text("Test"),
        // Text(widget.formDataCurriculum.toString()),
        // Text(widget.formDataCourses.toString()),
        // const SizedBox(
        //   height: 20,
        // ),
        Expanded(
            child: SingleChildScrollView(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: displaySequence(sequenceList[currentSequence]),
          ),
        )),
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            ElevatedButton(
                onPressed: () {
                  if (currentSequence > 0) {
                    setState(() {
                      currentSequence--;
                    });
                  }
                },
                child: Icon(Icons.keyboard_arrow_left)),
            SizedBox(
              width: 10,
            ),
            Text("${currentSequence + 1}/$totalSequences"),
            SizedBox(
              width: 10,
            ),
            ElevatedButton(
                onPressed: () {
                  if (currentSequence < totalSequences - 1) {
                    setState(() {
                      currentSequence++;
                    });
                  }
                },
                child: Icon(Icons.keyboard_arrow_right))
          ],
        ),
        Row(
          children: [
            ElevatedButton(
                onPressed: () {
                  widget.changePage(1);
                },
                child: const Text("Prev")),
            Spacer(),
            ElevatedButton(onPressed: () {}, child: Text("Save")),
            Spacer(),
            ElevatedButton(onPressed: () {}, child: Text("Finish")),
          ],
        ),
      ],
    );
  }
}
