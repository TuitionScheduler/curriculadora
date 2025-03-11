import 'package:curriculadora/drawer.dart';
import 'package:flutter/material.dart';

class GenerateSequence extends StatefulWidget {
  const GenerateSequence({super.key});

  @override
  State<GenerateSequence> createState() => _GenerateSequenceState();
}

class _GenerateSequenceState extends State<GenerateSequence> {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("New Curriculum"),
      ),
      drawer: const AppDrawer(),
      body: const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: <Widget>[
            Text(
              'This is the Generate Sequence Page',
            ),
          ],
        ),
      ),
    );
  }
}
