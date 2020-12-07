import { Component } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { AppComponent } from './app.component';
import { FooterComponent } from './components/footer/footer.component';
import { HeaderComponent } from './components/header/header.component';
import { MenuComponent } from './components/menu/menu.component';

@Component({ selector: 'app-header', template: '' })
class HeaderComponentStub implements Partial<HeaderComponent> { }

@Component({ selector: 'app-menu', template: '' })
class MenuComponentStub implements Partial<MenuComponent> { }

@Component({ selector: 'app-footer', template: '' })
class FooterComponentStub implements Partial<FooterComponent> { }

describe('AppComponent', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [AppComponent, HeaderComponentStub, MenuComponentStub, FooterComponentStub],
      imports: [RouterTestingModule],
    }).compileComponents();
  });

  it('should create the app', () => {
    const fixture = TestBed.createComponent(AppComponent);
    const app = fixture.componentInstance;
    expect(app).toBeTruthy();
  });

});
