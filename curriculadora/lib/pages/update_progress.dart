import 'package:flutter/material.dart';
import 'package:url_launcher/link.dart';

class UpdateProgress extends StatefulWidget {
  const UpdateProgress({super.key});

  @override
  State<UpdateProgress> createState() => _UpdateProgressState();
}

class _UpdateProgressState extends State<UpdateProgress> {
  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: <Widget>[
          const Text(
            'This is the Update Progress Page',
          ),
          const Text("(MOCKUP)"),
          const Text("Your current plan for the next semester is:\n"
              "Year: 2024, Term: Spring\n"
              "CIIC4151\n"
              "CIPO3011\n"
              "EDFU3012\n"
              "INME4045\n"
              "PSIC3002"),
          Link(
              uri: Uri.parse(
                  'https://matrical.site/?term=Spring&year=2024&courses=CIIC4151%2CCIPO3011%2CEDFU3012%2CINME4045%2CPSIC3002'), // hard-coded url
              target: LinkTarget.blank,
              builder: (context, followLink) => ElevatedButton(
                  onPressed: followLink,
                  child: const Text("Export to Matrical"))),
          const Divider(),
          Text("Is this still your plan?"),
          ElevatedButton(
              onPressed: () {},
              child: Text("Yes, continue with this semester")),
          SizedBox(
            height: 10,
          ),
          ElevatedButton(
              onPressed: () {}, child: Text("No, generate new sequence"))
        ],
      ),
    );
  }
}
