import { Component, EventEmitter, OnInit, Output } from '@angular/core';

export interface MetaStream {
  device: {
    model: string,
    manufacturer: string,
    category: string
  },
  fields: {
    id: string,
    name: string,
    description: string,
    dtype: string
  }[],
  streams: {
    name: string,
    description: string,
    unit: string,
    frequency?: number,
    channels: string[]
  }[]
}

@Component({
  selector: 'app-metadata-form',
  templateUrl: './metadata-form.component.html',
  styleUrls: ['./metadata-form.component.scss']
})
export class MetadataFormComponent implements OnInit {

  public metadata: MetaStream = {
    device: {
      model: '',
      manufacturer: '',
      category: ''
    },
    fields: [],
    streams: []
  };

  @Output() public onUpdate = new EventEmitter<MetaStream>();

  constructor() { }

  ngOnInit(): void {
  }

  public addNewStream() {
    this.metadata.streams.push({
      name: '',
      description: '',
      unit: '',
      frequency: null,
      channels: []
    })
  }

  public removeStream(i: number) {
    this.metadata.streams.splice(i, 1);
  }

}
