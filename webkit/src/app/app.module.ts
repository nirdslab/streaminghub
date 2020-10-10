// Angular Modules
import { BrowserModule } from '@angular/platform-browser';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { NgModule } from '@angular/core';
import { AppRoutingModule } from './app-routing.module';
// Material Modules
import { MatInputModule } from '@angular/material/input'
import { MatTabsModule } from '@angular/material/tabs';
// Application Components
import { AppComponent } from './app.component';
import { CanvasComponent } from './components/canvas/canvas.component';
import { EditorComponent } from './components/editor/editor.component';
import { MenuComponent } from './components/menu/menu.component';
import { HeaderComponent } from './components/header/header.component';
import { FooterComponent } from './components/footer/footer.component';
import { WidgetComponent } from './components/widget/widget.component';
import { DesignerComponent } from './views/designer/designer.component';

@NgModule({
  declarations: [
    AppComponent,
    CanvasComponent,
    EditorComponent,
    MenuComponent,
    HeaderComponent,
    FooterComponent,
    WidgetComponent,
    DesignerComponent
  ],
  imports: [
    BrowserModule,
    BrowserAnimationsModule,
    AppRoutingModule,
    MatInputModule,
    MatTabsModule
  ],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule { }
