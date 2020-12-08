import { Component, Input, OnInit } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';
import { filter } from 'rxjs/operators';
import { WebSocketService } from 'src/app/web-socket.service';
import { DialogComponent } from '../dialog/dialog.component';

@Component({
  selector: 'app-widget',
  templateUrl: './widget.component.html',
  styleUrls: ['./widget.component.scss']
})
export class WidgetComponent implements OnInit {

  @Input() public name: string;
  private selectedStreams: any[];

  constructor(
    public dialog: MatDialog,
    public snackbar: MatSnackBar,
    private ws: WebSocketService
  ) { }

  ngOnInit(): void {
    this.ws?.listen<any>().pipe(filter(res => res.command === 'search')).subscribe(
      res => { this.openDialog(res.data.streams); },
      _error => { this.snackbar.open("An error occurred when searching for streams.") }
    );
    this.ws?.listen<any>().pipe(filter(res => res.command === 'data')).subscribe(
      res => { console.dir(res); },
      _error => { this.snackbar.open("An error occurred when receiving data.") }
    );
  }

  onDoubleClick(event: Event) {
    event.preventDefault();
    this.ws.send<any>({ command: 'search' });
  }

  openDialog(streams: any[]) {
    const dialogRef = this.dialog?.open(DialogComponent, {
      data: { name: this.name, options: streams }
    });
    dialogRef?.afterClosed().subscribe((result: any[]) => {
      if (result) {
        this.selectedStreams = result.filter(x => x.selected);
        this.selectedStreams.forEach((stream: any) => {
          this.ws?.send<any>({ command: 'subscribe', data: { id: stream.id, name: stream.name, type: stream.type } });
        });
      }
    });
  }

}
