import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'local_store.dart';

class Api {
  static const defaultBase='http://10.0.2.2:8000';
  static String base=defaultBase;
  static String? token;
  static Future<void> init() async {
    final p=await SharedPreferences.getInstance();
    base=p.getString('api_base')??defaultBase;token=p.getString('token');
  }
  static Future<void> configure(String url) async {
    base=url.trim().replaceAll(RegExp(r'/$'),'');
    final p=await SharedPreferences.getInstance();await p.setString('api_base',base);
  }
  static Future<dynamic> request(String method,String path,{Map<String,dynamic>? body}) async {
    final uri=Uri.parse('$base$path');
    final headers={'Content-Type':'application/json',if(token!=null)'Authorization':'Bearer $token'};
    late http.Response r;
    if(method=='GET') r=await http.get(uri,headers:headers).timeout(const Duration(seconds:15));
    else if(method=='POST') r=await http.post(uri,headers:headers,body:jsonEncode(body??{})).timeout(const Duration(seconds:15));
    else if(method=='PUT') r=await http.put(uri,headers:headers,body:jsonEncode(body??{})).timeout(const Duration(seconds:15));
    else if(method=='DELETE') r=await http.delete(uri,headers:headers).timeout(const Duration(seconds:15));
    else r=await http.patch(uri,headers:headers,body:jsonEncode(body??{})).timeout(const Duration(seconds:15));
    final dynamic data=r.body.isEmpty?<String,dynamic>{}:jsonDecode(r.body);
    if(r.statusCode<200||r.statusCode>=300) throw Exception(data['detail']??'Server error ${r.statusCode}');
    return data;
  }
  static Future<void> login(String email,String password) async {
    final r=await request('POST','/auth/login',body:{'email':email,'password':password});
    token=r['access_token'];final p=await SharedPreferences.getInstance();await p.setString('token',token!);
  }
  static Future<int> syncPending(int shopId) async {
    final queue=await LocalStore.pending(); int done=0;
    for(final item in queue) {
      try {
        final payload=jsonDecode(item['payload'] as String) as Map<String,dynamic>;
        if(item['operation']=='upsert') {
          final result=await request('PUT','/shops/$shopId/records',body:payload);
          await LocalStore.cache(Map<String,dynamic>.from(result),shopId);
        }
        await LocalStore.removeQueue(item['id'] as int); done++;
      } catch (_) { break; }
    }
    return done;
  }
  static Future<void> logout() async {token=null;final p=await SharedPreferences.getInstance();await p.remove('token');}
}
