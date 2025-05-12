import 'package:flutter/material.dart';

class GenerateSequence extends StatefulWidget {
  const GenerateSequence({super.key});

  @override
  State<GenerateSequence> createState() => _GenerateSequenceState();
}

class _GenerateSequenceState extends State<GenerateSequence> {
  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: <Widget>[
          const Text(
            'You have no saved sequences',
          ),
          TextButton(
              onPressed: () {}, child: const Text("+ Generate new sequence"))
        ],
      ),
    );
  }
}
