import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-menu',
  templateUrl: './menu.component.html',
  styleUrls: ['./menu.component.scss']
})
export class MenuComponent implements OnInit {

  public links = [{title: 'Metadata', link: '/metadata'}, {title: 'Designer', link: '/designer'}];
  public activeLink = this.links[0];

  constructor() { }

  ngOnInit(): void {
  }

}
