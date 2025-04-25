import 'package:curriculadora/models/reading-test.dart';
import 'package:flutter/material.dart';

class DisplaySequence extends StatefulWidget {
  const DisplaySequence({super.key});

  @override
  State<DisplaySequence> createState() => _DisplaySequenceState();
}

class _DisplaySequenceState extends State<DisplaySequence> {
  List<Widget> readDB() {
    List<Widget> semesterList = [];
    Map<String, Map<String, dynamic>> sequence = testSequence();
    Map<String, Map<String, dynamic>> courses = testCourses();
    Iterable<String> terms = sequence.keys;
    for (final term in terms) {
      List<Widget> courseList = [];
      courseList.add(Row(
        children: [
          Text(term, style: TextStyle(color: Colors.black.withOpacity(0.5))),
        ],
      ));
      courseList.add(
        const SizedBox(
          height: 5,
        ),
      );

      for (int j = 0; j < sequence[term]!["courses"].length; j++) {
        String code = sequence[term]!["courses"][j];
        int req = courses[code]!["prerequisites"].length +
            courses[code]!["corequisites"].length;
        int reqFor = courses[code]!["prerequisite_for"].length +
            courses[code]!["corequisite_for"].length;
        courseList.add(displayRow(code, req, reqFor));
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
    semesterList.removeLast();
    return semesterList;
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

  @override
  Widget build(BuildContext context) {
    return Center(
      child: SingleChildScrollView(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: readDB(),
        ),
      ),
    );
  }
}

class ViewSequence extends StatefulWidget {
  const ViewSequence({super.key});

  @override
  State<ViewSequence> createState() => _ViewSequenceState();
}

class _ViewSequenceState extends State<ViewSequence> {
  @override
  Widget build(BuildContext context) {
    return DisplaySequence();
  }
}
