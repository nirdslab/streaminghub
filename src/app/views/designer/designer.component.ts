import { Component, OnInit } from '@angular/core';
import { WebSocketService } from 'src/app/web-socket.service';

@Component({
  selector: 'app-designer',
  templateUrl: './designer.component.html',
  styleUrls: ['./designer.component.scss']
})
export class DesignerComponent implements OnInit {

  constructor(private ws: WebSocketService) { }

  ngOnInit(): void {
    this.ws.listen<any>().subscribe(res => {
      this.handleResponse(res);
    })
    this.ws.send<any>({ command: 'search' });
  }

  private handleResponse(res: WSResponse<any>) {
    console.dir(res);
    switch (res.command) {
      case "search":
        const streams: any[] = res.data.streams;
        const ids: string[] = streams.map(s => s.id);
        ids.forEach(id => {
          console.log(id);
          this.ws.send<any>({ command: 'subscribe', data: { id } });
        })
        break;
    }
  }

}
