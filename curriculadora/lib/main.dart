import 'package:curriculadora/drawer.dart';
import 'package:curriculadora/pages/generate_sequence.dart';
import 'package:curriculadora/pages/sequence_view.dart';
import 'package:curriculadora/pages/update_progress.dart';
import 'package:flutter/material.dart';
import 'package:url_launcher/link.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  // This widget is the root of your application.
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Flutter Demo',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.indigo),
        useMaterial3: true,
      ),
      // home: const MyHomePage(title: 'Schedule'),
      initialRoute: "/",
      routes: {
        "/": (context) => SequenceView(),
        "/generate": (context) => GenerateSequence(),
        "/updateProgress": (context) => UpdateProgress()
      },
    );
  }
}

class MyHomePage extends StatefulWidget {
  const MyHomePage({super.key, required this.title});
  final String title;

  @override
  State<MyHomePage> createState() => _MyHomePageState();
}

class _MyHomePageState extends State<MyHomePage> {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
        title: Text(widget.title),
      ),
      drawer: AppDrawer(),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: <Widget>[
            const Text(
              'You have no curriculums set',
            ),
            Link(
                uri: Uri.parse(
                    'https://matrical.site/?term=Spring&year=2024&courses=CIIC4151%2CCIPO3011%2CEDFU3012%2CINME4045%2CPSIC3002'),
                builder: (context, followLink) => TextButton(
                    onPressed: followLink,
                    child: const Text("+ Generate curriculum")))
          ],
        ),
      ),
    );
  }
}
