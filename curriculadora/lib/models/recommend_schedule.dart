import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';

import 'package:http/http.dart' as http;

// Processes the HTTP query response and converts it into a List<Map<String, dynamic>>.
Map<String, dynamic> processQuery(http.Response response) {
  if (response.statusCode == 200) {
    print('Successfully returned HTTP query response!');
  } else {
    String customErrorMessage = '';
    throw Exception(
        'HTTP Request Failed. \n Status Code ${response.statusCode}: ${response.reasonPhrase}. \n $customErrorMessage');
  }

  Uint8List jsonResponse = response.bodyBytes;
  Map<String, dynamic> result =
      jsonDecode(const Utf8Decoder().convert(jsonResponse));
  return result;
}

Future<Map<String, dynamic>> getRecommendations(
    Map<String, dynamic> preferences) async {
  String backendAppUrl = 'http://127.0.0.1:8000/recommend-schedule';
  http.Response response = await http.post(Uri.parse(backendAppUrl),
      headers: {
        'Content-Type': 'application/json; charset=UTF-8',
        'Accept': '*/*'
      },
      body: jsonEncode(preferences));
  Map<String, dynamic> result = processQuery(response);
  return result;
}
