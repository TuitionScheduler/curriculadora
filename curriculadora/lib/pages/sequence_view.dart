import 'package:curriculadora/drawer.dart';
import 'package:flutter/material.dart';

class SequenceView extends StatefulWidget {
  const SequenceView({super.key});

  @override
  State<SequenceView> createState() => _SequenceViewState();
}

class _SequenceViewState extends State<SequenceView> {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Saved Sequences"),
      ),
      drawer: const AppDrawer(),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: <Widget>[
            const Text(
              'You have no saved sequences',
            ),
            TextButton(
                onPressed: () {
                  Navigator.pushNamed(context, "/generate");
                },
                child: const Text("+ Generate new sequence"))
          ],
        ),
      ),
    );
  }
}
