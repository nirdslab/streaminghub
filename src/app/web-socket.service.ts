import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { webSocket, WebSocketSubject } from 'rxjs/webSocket';

@Injectable({
  providedIn: 'root'
})
export class WebSocketService {

  private ws: WebSocketSubject<any> = webSocket<any>('ws://localhost:8765');

  constructor() {
    this.ws.subscribe();
  }

  public listen<T>(): Observable<WSResponse<T>> {
    return this.ws.pipe(map(x => <WSResponse<T>>x));
  }

  public send<T>(request: WSRequest<T>) {
    this.ws.next(request);
  }

}
