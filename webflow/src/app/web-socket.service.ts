import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { webSocket, WebSocketSubject } from 'rxjs/webSocket';

@Injectable({
  providedIn: 'root'
})
export class WebSocketService {

  private ws: WebSocketSubject<any>;

  constructor() {
    this.ws = webSocket<any>('ws://localhost:8765');
  }

  public listen<T>(): Observable<WSResponse<T>> {
    return this.ws;
  }

  public send<T>(request: WSRequest<T>) {
    this.ws.next(request);
  }

}
