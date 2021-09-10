import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { webSocket, WebSocketSubject } from 'rxjs/webSocket';

@Injectable({
  providedIn: 'root'
})
export class WebSocketService {

  private ws: WebSocketSubject<any>;

  constructor() {
    this.ws = webSocket<any>('wss://streaminghub-streaminghub-datamux-staging.35.222.43.57.nip.io/ws');
  }

  public setAddress(address: string): void {
    // TODO fix this
    if (this.ws?.observers.length > 0) {
      this.ws.complete();
    }
    this.ws = webSocket<any>(address);
  }

  public listen<T>(): Observable<WSResponse<T>> {
    return this.ws;
  }

  public send<T>(request: WSRequest<T>) {
    this.ws.next(request);
  }

}
