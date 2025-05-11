import 'package:curriculadora/pages/data_extraction.dart';
import 'package:flutter/material.dart';
import 'package:flutter_form_builder/flutter_form_builder.dart';

class DegreeForm extends StatefulWidget {
  final int index;

  const DegreeForm({super.key, required this.index});

  @override
  State<DegreeForm> createState() => _DegreeFormState();
}

class _DegreeFormState extends State<DegreeForm> {
  // late Future<List<Map<String, dynamic>>> program;
  List<String> degree = ["Bachelor's", "Master's", "Doctorate", "Minor"];
  List<String> term = ["S1", "S2", "V"];
  List<String> year = ["Y1", "Y2", "Y3", "Y4", "Y5", "Y6", "Y7", "Y8", "Y9"];
  List<String> difficulty = ["Flat", "Increasing", "Decreasing"];
  bool _loading = false;
  List<Map<String, dynamic>> programs = [];

  @override
  void initState() {
    super.initState();
    _fetchData();
  }

  Future<void> _fetchData() async {
    setState(() {
      _loading = true;
    });

    List<Map<String, dynamic>> results = [];

    try {
      results = await getAllRecordsFromTable('programs');
    } catch (e) {
      print('Query was unable to get record(s) from database: \n $e');
    }

    setState(() {
      programs = results;
      // print(programs.toString());
      // print(programs.length);
      _loading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    if (_loading == true) {
      return const CircularProgressIndicator();
    } else {
      return Column(
        mainAxisAlignment: MainAxisAlignment.start,
        children: <Widget>[
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Flexible(
                  child: Text(
                "Degree:",
                style: TextStyle(fontSize: 16),
              )),
              Flexible(
                  child: SizedBox(
                width: 15,
              )),
              Expanded(
                child: FormBuilderDropdown(
                  key: UniqueKey(),
                  name: 'degree${widget.index}',
                  initialValue: degree[0],
                  items: degree.map((option) {
                    return DropdownMenuItem(
                      value: option,
                      child: Text(option),
                    );
                  }).toList(),
                ),
              )
            ],
          ),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Flexible(
                  child: Text(
                "Study program:",
                style: TextStyle(fontSize: 16),
              )),
              // Flexible(
              //     child: SizedBox(
              //   width: 15,
              // )),
              Expanded(
                flex: 3,
                child: FormBuilderDropdown(
                  key: UniqueKey(),
                  name: 'program${widget.index}',
                  // initialValue: ,
                  items: programs.map((option) {
                    return DropdownMenuItem(
                      value: option["code"],
                      child: Text(option["name"].toString()),
                    );
                  }).toList(),
                ),
              )
            ],
          ),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Flexible(
                  flex: 3,
                  child: Text(
                    "Current year & term:",
                    style: TextStyle(fontSize: 16),
                  )),
              Flexible(
                  child: SizedBox(
                width: 8,
              )),
              Flexible(
                child: FormBuilderDropdown(
                    key: UniqueKey(),
                    name: 'startYear${widget.index}',
                    initialValue: year[0],
                    items: year.map((option) {
                      return DropdownMenuItem(
                        value: option,
                        child: Text(option),
                      );
                    }).toList()),
              ),
              Flexible(
                  child: SizedBox(
                width: 8,
              )),
              Flexible(
                  child: FormBuilderDropdown(
                      key: UniqueKey(),
                      name: 'startTerm${widget.index}',
                      initialValue: term[0],
                      items: term.map((option) {
                        return DropdownMenuItem(
                          value: option,
                          child: Text(option),
                        );
                      }).toList()))
            ],
          ),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Flexible(
                  flex: 3,
                  child: Text(
                    "Expected to graduate in:",
                    style: TextStyle(fontSize: 16),
                  )),
              Flexible(
                  child: SizedBox(
                width: 8,
              )),
              Flexible(
                child: FormBuilderDropdown(
                    key: UniqueKey(),
                    name: 'endYear${widget.index}',
                    initialValue: year[4],
                    items: year.map((option) {
                      return DropdownMenuItem(
                        value: option,
                        child: Text(option),
                      );
                    }).toList()),
              ),
              Flexible(
                  child: SizedBox(
                width: 8,
              )),
              Flexible(
                  child: FormBuilderDropdown(
                      key: UniqueKey(),
                      name: 'endTerm${widget.index}',
                      initialValue: term[1],
                      items: term.map((option) {
                        return DropdownMenuItem(
                          value: option,
                          child: Text(option),
                        );
                      }).toList()))
            ],
          ),
          SizedBox(
            height: 10,
          ),
        ],
      );
    }
  }
}

class AddCurriculum extends StatefulWidget {
  final int page;
  final Map<String, dynamic> formData;
  final Function(int newPage) changePage;
  final Function(Map<String, dynamic> formData) saveFormCurriculum;
  const AddCurriculum(
      {super.key,
      required this.page,
      required this.formData,
      required this.changePage,
      required this.saveFormCurriculum});

  @override
  State<AddCurriculum> createState() => _AddCurriculumState();
}

class _AddCurriculumState extends State<AddCurriculum> {
  final _formKey = GlobalKey<FormBuilderState>();
  List<String> program = ["CIIC", "INSO", "ICOM", "INEL", "ININ"];
  List<String> degree = ["Bachelor's", "Master's", "Doctorate", "Minor"];
  List<String> term = ["S1", "S2", "V"];
  List<String> year = ["Y1", "Y2", "Y3", "Y4", "Y5", "Y6", "Y7", "Y8", "Y9"];
  List<String> difficulty = ["Flat", "Increasing", "Decreasing"];
  late Map<String, dynamic> formData = {};

  // List<DegreeForm> degreeList = <DegreeForm>[];

  // void unregisterDegree(int i) {
  //   print(_formKey.currentState!.fields);
  //   print("Removing: $i");
  //   _formKey.currentState!.unregisterField(
  //       'degree$i', _formKey.currentState!.fields['degree$i']!);
  //   _formKey.currentState!.unregisterField(
  //       'program$i', _formKey.currentState!.fields['program$i']!);
  //   _formKey.currentState!.unregisterField(
  //       'startYear$i', _formKey.currentState!.fields['startYear$i']!);
  //   _formKey.currentState!.unregisterField(
  //       'startTerm$i', _formKey.currentState!.fields['startTerm$i']!);
  //   _formKey.currentState!.unregisterField(
  //       'endYear$i', _formKey.currentState!.fields['endYear$i']!);
  //   _formKey.currentState!.unregisterField(
  //       'endTerm$i', _formKey.currentState!.fields['endTerm$i']!);
  // }

  @override
  Widget build(BuildContext context) {
    if (widget.formData.entries.isNotEmpty) {
      _formKey.currentState?.patchValue(widget.formData);
    }

    return FormBuilder(
      key: _formKey,
      autovalidateMode: AutovalidateMode.onUnfocus,
      child: SingleChildScrollView(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.start,
          children: <Widget>[
            DegreeForm(index: 0),
            SizedBox(
              height: 10,
            ),
            Text("Preferences"),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Flexible(
                    child: Text(
                  "Difficulty Curve:",
                  style: TextStyle(fontSize: 16),
                )),
                Flexible(
                    child: SizedBox(
                  width: 15,
                )),
                Flexible(
                  child: FormBuilderDropdown(
                    name: 'difficultyCurve',
                    initialValue: difficulty[0],
                    items: difficulty.map((option) {
                      return DropdownMenuItem(
                        value: option,
                        child: Text(option),
                      );
                    }).toList(),
                  ),
                )
              ],
            ),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Flexible(
                    child: Text(
                  "Credits per semester:",
                  style: TextStyle(fontSize: 16),
                )),
                Flexible(
                    child: SizedBox(
                  width: 15,
                )),
                Flexible(
                  flex: 3,
                  child: FormBuilderRangeSlider(
                    name: 'creditLoad',
                    min: 3,
                    max: 21,
                    divisions: 18,
                    initialValue: RangeValues(12, 18),
                  ),
                )
              ],
            ),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Flexible(
                  child: FormBuilderSwitch(
                      name: 'summerClasses',
                      title: Text("Take Summer Classes?",
                          style: TextStyle(fontSize: 16))),
                )
              ],
            ),
            SizedBox(
              height: 10,
            ),
            ElevatedButton(
                onPressed: () {
                  _formKey.currentState?.save();
                  formData = _formKey.currentState!.value;
                  ScaffoldMessenger.of(context).removeCurrentSnackBar();
                  ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text(formData.toString())));
                },
                child: Text("Save")),
            ElevatedButton(
                onPressed: () {
                  _formKey.currentState?.save();
                  formData = _formKey.currentState!.value;
                  widget.saveFormCurriculum(formData);
                  widget.changePage(1);
                },
                child: Text("Next"))
          ],
        ),
      ),
    );
  }
}
