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
            'This is the current plan for your next semester.',
          ),
          Container(
            decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(5),
                color: Colors.white,
                boxShadow: [
                  BoxShadow(
                      blurRadius: 1,
                      offset: Offset(1, 1),
                      color: Colors.black12)
                ]),
            width: MediaQuery.sizeOf(context).width - 60,
            child: Padding(
              padding: EdgeInsets.all(10),
              child: Column(
                children: [
                  Row(
                    children: [
                      Text("Spring2026",
                          style:
                              TextStyle(color: Colors.black.withOpacity(0.5))),
                    ],
                  ),
                  SizedBox(
                    height: 5,
                  ),
                  Row(
                    children: [
                      Text("MATE3032"),
                      Spacer(),
                      RichText(
                          text: TextSpan(children: [
                        WidgetSpan(child: Icon(Icons.lock)),
                        TextSpan(text: "1 "),
                        WidgetSpan(child: Icon(Icons.key)),
                        TextSpan(text: "2")
                      ])),
                    ],
                  ),
                  Divider(),
                  Row(
                    children: [
                      Text("QUIM3132"),
                      Spacer(),
                      RichText(
                          text: TextSpan(children: [
                        WidgetSpan(child: Icon(Icons.lock)),
                        TextSpan(text: "3 "),
                        WidgetSpan(child: Icon(Icons.key)),
                        TextSpan(text: "1")
                      ])),
                    ],
                  ),
                  Divider(),
                  Row(
                    children: [
                      Text("QUIM3134"),
                      Spacer(),
                      RichText(
                          text: TextSpan(children: [
                        WidgetSpan(child: Icon(Icons.lock)),
                        TextSpan(text: "2 "),
                        WidgetSpan(child: Icon(Icons.key)),
                        TextSpan(text: "1")
                      ])),
                    ],
                  ),
                  Divider(),
                  Row(
                    children: [
                      Text("INGL3102"),
                      Spacer(),
                      RichText(
                          text: TextSpan(children: [
                        WidgetSpan(child: Icon(Icons.lock)),
                        TextSpan(text: "0 "),
                        WidgetSpan(child: Icon(Icons.key)),
                        TextSpan(text: "0")
                      ])),
                    ],
                  ),
                  Divider(),
                  Row(
                    children: [
                      Text("CIIC3075"),
                      Spacer(),
                      RichText(
                          text: TextSpan(children: [
                        WidgetSpan(child: Icon(Icons.lock)),
                        TextSpan(text: "1 "),
                        WidgetSpan(child: Icon(Icons.key)),
                        TextSpan(text: "3")
                      ])),
                    ],
                  ),
                  Divider(),
                  Row(
                    children: [
                      Text("CIIC4010"),
                      Spacer(),
                      RichText(
                          text: TextSpan(children: [
                        WidgetSpan(child: Icon(Icons.lock)),
                        TextSpan(text: "1 "),
                        WidgetSpan(child: Icon(Icons.key)),
                        TextSpan(text: "3")
                      ])),
                    ],
                  )
                ],
              ),
            ),
          ),
          SizedBox(
            height: 10,
          ),
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
