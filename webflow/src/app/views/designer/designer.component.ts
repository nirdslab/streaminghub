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
      if (res.error) {
        console.error('error', res.error);
      }
      if (res.data) {
        console.log('data', res.data);
      }
    })
    this.ws.send<any>({ command: 'search' });
  }

}
