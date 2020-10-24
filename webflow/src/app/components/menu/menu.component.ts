import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, NavigationEnd, Router } from '@angular/router';
import { filter } from "rxjs/operators";

@Component({
  selector: 'app-menu',
  templateUrl: './menu.component.html',
  styleUrls: ['./menu.component.scss']
})
export class MenuComponent implements OnInit {

  public links = [{ title: 'Metadata', link: '/metadata' }, { title: 'Designer', link: '/designer' }];
  public activeLink: string;

  constructor(activatedRoute: ActivatedRoute, router: Router) {
    router.events.pipe(filter(e => e instanceof NavigationEnd)).subscribe((e: any) => {
      this.activeLink = e.urlAfterRedirects;
    })
  }

  ngOnInit(): void {
  }

}
