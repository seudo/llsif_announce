ROOT = "/tmp2/lovelive/"

URI = {
  "authkey" : "/main.php/login/authkey",
  "login" : "/main.php/login/login",
  "web_index" : "/webview.php/announce/index?disp_faulty=%s",
  "web_detail" : "/webview.php/announce/detail?0=&announce_id=%s&disp_faulty=%s",
  "page_detail" : "/webview.php/static?id=%s",

  "user_info" : "/main.php/user/userInfo",
  "rank_event" : "/main.php/ranking/eventPlayer", 
  }

HEADER = {
    "Accept": "*/*",
    "Accept-Encoding": "gzip,deflate",
    "API-Model": "straightforward",
    "Debug": "1",
    "Client-Version": "1.3.9",
    "Time-Zone": "CST",
    "Region": "392",
}

Platform = dict(
    iOS = {"OS-Version": "iPhone 6 CDMA 8.2.1", "OS": "iOS", "Platform-Type": "1"},
    Android = {"OS-Version": "MI 2S Xiaomi MSM8960 4.1.1", "OS": "Android","Platform-Type": "2"})
