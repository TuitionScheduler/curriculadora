import 'package:flutter/material.dart';

class GenerateSequence extends StatefulWidget {
  const GenerateSequence({super.key});

  @override
  State<GenerateSequence> createState() => _GenerateSequenceState();
}

class _GenerateSequenceState extends State<GenerateSequence> {
  @override
  Widget build(BuildContext context) {
    return const Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: <Widget>[
          Text(
            'This is the Generate Sequence Page',
          ),
        ],
      ),
    );
  }
}
