import 'package:flutter/material.dart';

class ViewSequence extends StatefulWidget {
  const ViewSequence({super.key});

  @override
  State<ViewSequence> createState() => _ViewSequenceState();
}

class _ViewSequenceState extends State<ViewSequence> {
  @override
  Widget build(BuildContext context) {
    return Center(
      child: SingleChildScrollView(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: <Widget>[
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
              width: MediaQuery.sizeOf(context).width - 30,
              child: Padding(
                padding: EdgeInsets.all(10),
                child: Column(
                  children: [
                    Row(
                      children: [
                        Text("Y1S1",
                            style: TextStyle(
                                color: Colors.black.withOpacity(0.5))),
                      ],
                    ),
                    SizedBox(
                      height: 5,
                    ),
                    Row(
                      children: [
                        Text("MATE 3031"),
                        Spacer(),
                        RichText(
                            text: TextSpan(children: [
                          WidgetSpan(child: Icon(Icons.lock)),
                          TextSpan(text: "1 "),
                          WidgetSpan(child: Icon(Icons.key)),
                          TextSpan(text: "0")
                        ])),
                      ],
                    ),
                    Divider(),
                    Row(
                      children: [
                        Text("QUIM 3131"),
                        Spacer(),
                        RichText(
                            text: TextSpan(children: [
                          WidgetSpan(child: Icon(Icons.lock)),
                          TextSpan(text: "1 "),
                          WidgetSpan(child: Icon(Icons.key)),
                          TextSpan(text: "0")
                        ])),
                      ],
                    ),
                    Divider(),
                    Row(
                      children: [
                        Text("QUIM 3133"),
                        Spacer(),
                        RichText(
                            text: TextSpan(children: [
                          WidgetSpan(child: Icon(Icons.lock)),
                          TextSpan(text: "1 "),
                          WidgetSpan(child: Icon(Icons.key)),
                          TextSpan(text: "0")
                        ])),
                      ],
                    ),
                    Divider(),
                    Row(
                      children: [
                        Text("INGL 3101"),
                        Spacer(),
                        RichText(
                            text: TextSpan(children: [
                          WidgetSpan(child: Icon(Icons.lock)),
                          TextSpan(text: "1 "),
                          WidgetSpan(child: Icon(Icons.key)),
                          TextSpan(text: "0")
                        ])),
                      ],
                    ),
                    Divider(),
                    Row(
                      children: [
                        Text("CIIC 3015"),
                        Spacer(),
                        RichText(
                            text: TextSpan(children: [
                          WidgetSpan(child: Icon(Icons.lock)),
                          TextSpan(text: "1 "),
                          WidgetSpan(child: Icon(Icons.key)),
                          TextSpan(text: "0")
                        ])),
                      ],
                    ),
                  ],
                ),
              ),
            ),
            SizedBox(
              height: 10,
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
              width: MediaQuery.sizeOf(context).width - 30,
              child: Padding(
                padding: EdgeInsets.all(10),
                child: Column(
                  children: [
                    Row(
                      children: [
                        Text("Y1S2",
                            style: TextStyle(
                                color: Colors.black.withOpacity(0.5))),
                      ],
                    ),
                    SizedBox(
                      height: 5,
                    ),
                    Row(
                      children: [
                        Text("MATE 3032"),
                        Spacer(),
                        RichText(
                            text: TextSpan(children: [
                          WidgetSpan(child: Icon(Icons.lock)),
                          TextSpan(text: "1 "),
                          WidgetSpan(child: Icon(Icons.key)),
                          TextSpan(text: "0")
                        ])),
                      ],
                    ),
                    Divider(),
                    Row(
                      children: [
                        Text("QUIM 3132"),
                        Spacer(),
                        RichText(
                            text: TextSpan(children: [
                          WidgetSpan(child: Icon(Icons.lock)),
                          TextSpan(text: "1 "),
                          WidgetSpan(child: Icon(Icons.key)),
                          TextSpan(text: "0")
                        ])),
                      ],
                    ),
                    Divider(),
                    Row(
                      children: [
                        Text("QUIM 3134"),
                        Spacer(),
                        RichText(
                            text: TextSpan(children: [
                          WidgetSpan(child: Icon(Icons.lock)),
                          TextSpan(text: "1 "),
                          WidgetSpan(child: Icon(Icons.key)),
                          TextSpan(text: "0")
                        ])),
                      ],
                    ),
                    Divider(),
                    Row(
                      children: [
                        Text("INGL 3102"),
                        Spacer(),
                        RichText(
                            text: TextSpan(children: [
                          WidgetSpan(child: Icon(Icons.lock)),
                          TextSpan(text: "1 "),
                          WidgetSpan(child: Icon(Icons.key)),
                          TextSpan(text: "0")
                        ])),
                      ],
                    ),
                    Divider(),
                    Row(
                      children: [
                        Text("CIIC 3075"),
                        Spacer(),
                        RichText(
                            text: TextSpan(children: [
                          WidgetSpan(child: Icon(Icons.lock)),
                          TextSpan(text: "1 "),
                          WidgetSpan(child: Icon(Icons.key)),
                          TextSpan(text: "0")
                        ])),
                      ],
                    ),
                    Divider(),
                    Row(
                      children: [
                        Text("CIIC 4010"),
                        Spacer(),
                        RichText(
                            text: TextSpan(children: [
                          WidgetSpan(child: Icon(Icons.lock)),
                          TextSpan(text: "1 "),
                          WidgetSpan(child: Icon(Icons.key)),
                          TextSpan(text: "0")
                        ])),
                      ],
                    ),
                  ],
                ),
              ),
            ),
            SizedBox(
              height: 10,
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
              width: MediaQuery.sizeOf(context).width - 30,
              child: Padding(
                padding: EdgeInsets.all(10),
                child: Column(
                  children: [
                    Row(
                      children: [
                        Text("Y2S1",
                            style: TextStyle(
                                color: Colors.black.withOpacity(0.5))),
                      ],
                    ),
                    SizedBox(
                      height: 5,
                    ),
                    Row(
                      children: [
                        Text("MATE 3063"),
                        Spacer(),
                        RichText(
                            text: TextSpan(children: [
                          WidgetSpan(child: Icon(Icons.lock)),
                          TextSpan(text: "1 "),
                          WidgetSpan(child: Icon(Icons.key)),
                          TextSpan(text: "0")
                        ])),
                      ],
                    ),
                    Divider(),
                    Row(
                      children: [
                        Text("FISI 3171"),
                        Spacer(),
                        RichText(
                            text: TextSpan(children: [
                          WidgetSpan(child: Icon(Icons.lock)),
                          TextSpan(text: "1 "),
                          WidgetSpan(child: Icon(Icons.key)),
                          TextSpan(text: "0")
                        ])),
                      ],
                    ),
                    Divider(),
                    Row(
                      children: [
                        Text("FISI 3173"),
                        Spacer(),
                        RichText(
                            text: TextSpan(children: [
                          WidgetSpan(child: Icon(Icons.lock)),
                          TextSpan(text: "1 "),
                          WidgetSpan(child: Icon(Icons.key)),
                          TextSpan(text: "0")
                        ])),
                      ],
                    ),
                    Divider(),
                    Row(
                      children: [
                        Text("CIIC 4020"),
                        Spacer(),
                        RichText(
                            text: TextSpan(children: [
                          WidgetSpan(child: Icon(Icons.lock)),
                          TextSpan(text: "1 "),
                          WidgetSpan(child: Icon(Icons.key)),
                          TextSpan(text: "0")
                        ])),
                      ],
                    ),
                    Divider(),
                    Row(
                      children: [
                        Text("ESPA 3101"),
                        Spacer(),
                        RichText(
                            text: TextSpan(children: [
                          WidgetSpan(child: Icon(Icons.lock)),
                          TextSpan(text: "1 "),
                          WidgetSpan(child: Icon(Icons.key)),
                          TextSpan(text: "0")
                        ])),
                      ],
                    ),
                  ],
                ),
              ),
            ),
            SizedBox(
              height: 10,
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
              width: MediaQuery.sizeOf(context).width - 30,
              child: Padding(
                padding: EdgeInsets.all(10),
                child: Column(
                  children: [
                    Row(
                      children: [
                        Text("Y2S2",
                            style: TextStyle(
                                color: Colors.black.withOpacity(0.5))),
                      ],
                    ),
                    SizedBox(
                      height: 5,
                    ),
                    Row(
                      children: [
                        Text("CIIC 4025"),
                        Spacer(),
                        RichText(
                            text: TextSpan(children: [
                          WidgetSpan(child: Icon(Icons.lock)),
                          TextSpan(text: "1 "),
                          WidgetSpan(child: Icon(Icons.key)),
                          TextSpan(text: "0")
                        ])),
                      ],
                    ),
                    Divider(),
                    Row(
                      children: [
                        Text("FISI 3172"),
                        Spacer(),
                        RichText(
                            text: TextSpan(children: [
                          WidgetSpan(child: Icon(Icons.lock)),
                          TextSpan(text: "1 "),
                          WidgetSpan(child: Icon(Icons.key)),
                          TextSpan(text: "0")
                        ])),
                      ],
                    ),
                    Divider(),
                    Row(
                      children: [
                        Text("FISI 3174"),
                        Spacer(),
                        RichText(
                            text: TextSpan(children: [
                          WidgetSpan(child: Icon(Icons.lock)),
                          TextSpan(text: "1 "),
                          WidgetSpan(child: Icon(Icons.key)),
                          TextSpan(text: "0")
                        ])),
                      ],
                    ),
                    Divider(),
                    Row(
                      children: [
                        Text("INEL 3105"),
                        Spacer(),
                        RichText(
                            text: TextSpan(children: [
                          WidgetSpan(child: Icon(Icons.lock)),
                          TextSpan(text: "1 "),
                          WidgetSpan(child: Icon(Icons.key)),
                          TextSpan(text: "0")
                        ])),
                      ],
                    ),
                    Divider(),
                    Row(
                      children: [
                        Text("ESPA 3102"),
                        Spacer(),
                        RichText(
                            text: TextSpan(children: [
                          WidgetSpan(child: Icon(Icons.lock)),
                          TextSpan(text: "1 "),
                          WidgetSpan(child: Icon(Icons.key)),
                          TextSpan(text: "0")
                        ])),
                      ],
                    ),
                  ],
                ),
              ),
            ),
            SizedBox(
              height: 10,
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
              width: MediaQuery.sizeOf(context).width - 30,
              child: Padding(
                padding: EdgeInsets.all(10),
                child: Column(
                  children: [
                    Row(
                      children: [
                        Text("Y3S1",
                            style: TextStyle(
                                color: Colors.black.withOpacity(0.5))),
                      ],
                    ),
                    SizedBox(
                      height: 5,
                    ),
                    Row(
                      children: [
                        Text("INSO 4101"),
                        Spacer(),
                        RichText(
                            text: TextSpan(children: [
                          WidgetSpan(child: Icon(Icons.lock)),
                          TextSpan(text: "1 "),
                          WidgetSpan(child: Icon(Icons.key)),
                          TextSpan(text: "0")
                        ])),
                      ],
                    ),
                    Divider(),
                    Row(
                      children: [
                        Text("CIIC 3081"),
                        Spacer(),
                        RichText(
                            text: TextSpan(children: [
                          WidgetSpan(child: Icon(Icons.lock)),
                          TextSpan(text: "1 "),
                          WidgetSpan(child: Icon(Icons.key)),
                          TextSpan(text: "0")
                        ])),
                      ],
                    ),
                    Divider(),
                    Row(
                      children: [
                        Text("MATE 4145"),
                        Spacer(),
                        RichText(
                            text: TextSpan(children: [
                          WidgetSpan(child: Icon(Icons.lock)),
                          TextSpan(text: "1 "),
                          WidgetSpan(child: Icon(Icons.key)),
                          TextSpan(text: "0")
                        ])),
                      ],
                    ),
                    Divider(),
                    Row(
                      children: [
                        Text("INEL 4115"),
                        Spacer(),
                        RichText(
                            text: TextSpan(children: [
                          WidgetSpan(child: Icon(Icons.lock)),
                          TextSpan(text: "1 "),
                          WidgetSpan(child: Icon(Icons.key)),
                          TextSpan(text: "0")
                        ])),
                      ],
                    ),
                    Divider(),
                    Row(
                      children: [
                        Text("INGL 3201"),
                        Spacer(),
                        RichText(
                            text: TextSpan(children: [
                          WidgetSpan(child: Icon(Icons.lock)),
                          TextSpan(text: "1 "),
                          WidgetSpan(child: Icon(Icons.key)),
                          TextSpan(text: "0")
                        ])),
                      ],
                    ),
                  ],
                ),
              ),
            ),
            SizedBox(
              height: 10,
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
              width: MediaQuery.sizeOf(context).width - 30,
              child: Padding(
                padding: EdgeInsets.all(10),
                child: Column(
                  children: [
                    Row(
                      children: [
                        Text("Y3S2",
                            style: TextStyle(
                                color: Colors.black.withOpacity(0.5))),
                      ],
                    ),
                    SizedBox(
                      height: 5,
                    ),
                    Row(
                      children: [
                        Text("INGE 3011"),
                        Spacer(),
                        RichText(
                            text: TextSpan(children: [
                          WidgetSpan(child: Icon(Icons.lock)),
                          TextSpan(text: "1 "),
                          WidgetSpan(child: Icon(Icons.key)),
                          TextSpan(text: "0")
                        ])),
                      ],
                    ),
                    Divider(),
                    Row(
                      children: [
                        Text("CIIC 4082"),
                        Spacer(),
                        RichText(
                            text: TextSpan(children: [
                          WidgetSpan(child: Icon(Icons.lock)),
                          TextSpan(text: "1 "),
                          WidgetSpan(child: Icon(Icons.key)),
                          TextSpan(text: "0")
                        ])),
                      ],
                    ),
                    Divider(),
                    Row(
                      children: [
                        Text("CIIC 5---"),
                        Spacer(),
                        RichText(
                            text: TextSpan(children: [
                          WidgetSpan(child: Icon(Icons.lock)),
                          TextSpan(text: "1 "),
                          WidgetSpan(child: Icon(Icons.key)),
                          TextSpan(text: "0")
                        ])),
                      ],
                    ),
                    Divider(),
                    Row(
                      children: [
                        Text("ININ 4010"),
                        Spacer(),
                        RichText(
                            text: TextSpan(children: [
                          WidgetSpan(child: Icon(Icons.lock)),
                          TextSpan(text: "1 "),
                          WidgetSpan(child: Icon(Icons.key)),
                          TextSpan(text: "0")
                        ])),
                      ],
                    ),
                    Divider(),
                    Row(
                      children: [
                        Text("INGL 3202"),
                        Spacer(),
                        RichText(
                            text: TextSpan(children: [
                          WidgetSpan(child: Icon(Icons.lock)),
                          TextSpan(text: "1 "),
                          WidgetSpan(child: Icon(Icons.key)),
                          TextSpan(text: "0")
                        ])),
                      ],
                    ),
                  ],
                ),
              ),
            ),
            SizedBox(
              height: 10,
            ),
          ],
        ),
      ),
    );
  }
}
