# gallery-dl_sjva

# TODO:
중복체크 해야함
로그 깔끔하게 정리 // 해결함
queue페이지에서 socket통신 안되는거 해결 // 해결함 

# 로직 구성도

다운로드:
gallery-dl_request.html -> /ajax/download_by_request ->

plugin.py -> Logic.download_by_request({url: url}) ->

logic.py -> {
  url exists:
    LogicQueue.add_queue(url)
} ->

logic_queue.py -> add_queue -> {
  entity = ModelGalleryDlItem.init(url)
  
  LogicQueue.entity_list에 이미 있으면(다운로드 중이나 실패했거나 완료했거나):
    이미 있는 항목 삭제(다시 다운받는다)
  
  LogicQueue.entity_list.append(entity)
  LogicQueue.download_queue.put(entity)
} ->

logic_queue.py -> download_thread_function -> {
  download_queue에서 하나 꺼내서 다운로드하고 tack_done()상태로
  LogicGalleryDL.download(entity)

} ->

logic_gallerydl.py -> download -> {

}
