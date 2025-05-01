import 'package:flutter/material.dart';
import 'dart:async';
import 'package:http/http.dart' as http;
import 'dart:convert';

// Processes the HTTP query response and converts it into a List<Map<String, dynamic>>.
List<Map<String, dynamic>> processQuery(http.Response response, [String tableName = '', String columnName = '', dynamic data = Null]) {
  if (response.statusCode == 200) {
    print('Successfully returned HTTP query response!');
  } 

  else {
    String customErrorMessage = '';
    if (tableName.isNotEmpty && columnName.isNotEmpty && data != Null) {
      customErrorMessage = 'Are you sure "$columnName : $data" from "$tableName" table exists in the database?';
    }
    else if (tableName.isNotEmpty && columnName.isNotEmpty) {
      customErrorMessage = 'Are you sure column "$columnName" from "$tableName" table exists in the database?';
    }
    else if (tableName.isNotEmpty) {
      customErrorMessage = 'Are you sure "$tableName" table exists in the database?';
    }
    throw Exception('HTTP Request Failed. \n Status Code ${response.statusCode}: ${response.reasonPhrase}. \n $customErrorMessage');
  }

  String jsonResponse = response.body;

  // For debugging if the right data type was returned
  // if (jsonResponse is Map){
  //   print('$jsonResponse is a Map');
  // }
  // else {
  //   print('$jsonResponse is not a Map');
  // }

  List<dynamic> responseList = jsonDecode(jsonResponse);

  // Converts each record in the response list to a Map<String, dynamic> 
  // and then adds them to a List<Map>
  List<Map<String, dynamic>> result = responseList
    .map((item) => item as Map<String, dynamic>)
    .toList();
  
  return result;
  
  // Ignore for now
  // if (result.isNotEmpty) {
  //   print('Successfully retreived query result!');
  //   return result;
  // }
  // else {
  //   // print('Table $tableName not found in courses.db');
  //   throw Exception('Table $tableName not found in courses.db'); 
  // }
}


// Queries the database for all the data records within a specified table (with all their fields (columns))
Future<List<Map<String, dynamic>>> getAllRecordsFromTable(String tableName) async {
  print('Getting all records from $tableName table...');

  String backendAppUrl = 'https://curriculadora-db-app-c1d0a13ccbf0.herokuapp.com';
  http.Response response = await http.get(Uri.parse('$backendAppUrl/table/$tableName'));

  List<Map<String, dynamic>> result = processQuery(response, tableName);
  return result;
}


// Queries the database for all the data records within a specified table (with all their fields (columns))
Future<List<Map<String, dynamic>>> getAllRecordsFromColumn(String tableName, String columnName) async {
  print('Getting all records from column $columnName in $tableName table...');

  String backendAppUrl = 'https://curriculadora-db-app-c1d0a13ccbf0.herokuapp.com';
  // http.Response response = await http.get(Uri.parse('$backendAppUrl/query?table=tableName&column=columnName'));
  http.Response response = await http.get(Uri.parse('$backendAppUrl/table/$tableName/$columnName'));

  List<Map<String, dynamic>> result = processQuery(response, tableName, columnName);
  return result;
}


// Queries the database for a specific data element 
Future<List<Map<String, dynamic>>> getRecord(String tableName, String columnName, dynamic data) async {
  print('Getting $columnName : $data from $tableName table...');

  String backendAppUrl = 'https://curriculadora-db-app-c1d0a13ccbf0.herokuapp.com';
  http.Response response = await http.get(Uri.parse('$backendAppUrl/table/$tableName/$columnName/$data'));

  List<Map<String, dynamic>> result = processQuery(response, tableName, columnName, data);
  return result;
}


// Ignore for now 
// // Queries the database for all the data records within a specified table (with all their fields (columns))
// Future<List<Map<String, dynamic>>> getAllRecordsFromDB(String tableName) async {
//   print('Getting all records from $tableName table...');
//   List<Map<String, dynamic>> result = [];
//   if (kIsWeb){
//     print('Identified web platform');
//     result = await getAllRecordsFromDBWeb(tableName);
//     print('Web Query Result is of type ${result.runtimeType}');
//   }
//   else if (PlatformIs.android || PlatformIs.iOS) {
//     print('Identified mobile device');
//     result = await getAllRecordsFromDBMobile(tableName);
//     print('Mobile Query Result is of type ${result.runtimeType}');
//   }

//   if (result.isNotEmpty) {
//     print('Successfully retreived query result!');
//     return result;
//   }
//   else {
//     // print('Table $tableName not found in courses.db');
//     throw Exception('Table $tableName not found in courses.db'); 
//   }
// }


// // Queries the database for all the data records within a specified column 
// Future<List<Map<String, dynamic>>> getAllRecordsFromDBColumn(String tableName, String columnName) async {
//   print('Getting all records from column $columnName in $tableName table...');
//   List<Map<String, dynamic>> result = [];
//   if (kIsWeb){
//     print('Identified web platform');
//     result = await getAllRecordsFromDBColumnWeb(tableName, columnName);
//   }
//   else if (PlatformIs.android || PlatformIs.iOS) {
//     print('Identified mobile device');
//     result = await getAllRecordsFromDBColumnMobile(tableName, columnName);
//   }

//   if (result.isNotEmpty) {
//     print('Successfully retreived query result!');
//     return result;
//   }
//   else {
//     // print('Column $columnName not found in $tableName table');
//     throw Exception('Column $columnName not found in $tableName table'); 
//   }
// }


// // Queries the database for a specific data element 
// Future<List<Map<String, dynamic>>> getDataFromDB(String tableName, String columnName, dynamic data) async {
//   print('Getting $columnName : $data from $tableName table...');
//   List<Map<String, dynamic>> result = [];
//   if (kIsWeb) {
//     print('Identified web platform');
//     result = await getDataFromDBWeb(tableName, columnName, data);
//   }
//   else if (PlatformIs.android || PlatformIs.iOS) {
//     print('Identified mobile device');
//     result = await getDataFromDBMobile(tableName, columnName, data);
//   }

//   if (result.isNotEmpty) {
//     print('Successfully retreived query result!');
//     return result;
//   }
//   else {
//     // print('$columnName : $data not found in $tableName table');
//     throw Exception('$columnName : $data not found in $tableName table'); 
//   }
// }


class DataExtraction extends StatefulWidget {
  const DataExtraction({super.key});

  @override
  State<DataExtraction> createState() => _DataExtractionState();
}

class _DataExtractionState extends State<DataExtraction> {
  @override
  void initState() {
    super.initState();
  }


  List<Map<String, dynamic>> _dbResults = [];
  bool _loading = false;

  Future<void> _fetchData() async {
    setState(() {
      _loading = true;
    });

    List<Map<String, dynamic>> results = [];

    try {

      results = await getRecord('courses', 'course_code', 'CIIC3015');

      // results = await getAllRecordsFromTable('Buildings');

      // results = await getAllRecordsFromColumn('courses', 'TA');

      // This error catch still has issues, not sure why yet...
      // results = await getRecord('courses', 'course_code', 'GAST3101');
    } 
    catch (e) {
      print('Query was unable to get record(s) from database: \n $e');
    }
    
    setState(() {
      _dbResults = results;
      _loading = false;
    });
  }


  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: <Widget>[
          const Text(
            'This is the Data Extraction Page',
          ),
          ElevatedButton(
              onPressed: _fetchData,
              child: Text("Trigger Database Query")),
          SizedBox(
            height: 10,
          ),          
          // Show loading indicator
          if (_loading) CircularProgressIndicator(),

          // Display results
          if (_dbResults.isNotEmpty)
            Padding(
              padding: const EdgeInsets.all(20.0),
              child: _buildTable(),
            ),
        ],
      ),
    );
  }


  Widget _buildTable() {
    final columns = _dbResults.first.keys.toList();

    return DataTable(
      columns: columns.map((col) => DataColumn(label: Text(col))).toList(),
      rows: _dbResults
          .map(
            (row) => DataRow(
              cells: columns
                  .map((col) => DataCell(Text(row[col].toString())))
                  .toList(),
            ),
          )
          .toList(),
    );
  }
}