import 'package:flutter/material.dart';
import 'package:flutter_form_builder/flutter_form_builder.dart';

class AddCurriculum extends StatefulWidget {
  const AddCurriculum({super.key});

  @override
  State<AddCurriculum> createState() => _AddCurriculumState();
}

class DegreeForm extends StatefulWidget {
  final int index;

  const DegreeForm({super.key, required this.index});

  @override
  State<DegreeForm> createState() => _DegreeFormState();
}

class _DegreeFormState extends State<DegreeForm> {
  List<String> program = ["CIIC", "INSO", "ICOM", "INEL", "ININ"];
  List<String> degree = ["Bachelor's", "Master's", "Doctorate", "Minor"];
  List<String> term = ["S1", "S2", "V"];
  List<String> year = ["Y1", "Y2", "Y3", "Y4", "Y5", "Y6", "Y7", "Y8", "Y9"];
  List<String> difficulty = ["Flat", "Increasing", "Decreasing"];

  @override
  Widget build(BuildContext context) {
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
                initialValue: program[0],
                items: program.map((option) {
                  return DropdownMenuItem(
                    value: option,
                    child: Text(option.toString()),
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
          ],
        ),
      ),
    );
  }
}
