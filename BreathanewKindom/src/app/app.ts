import { Component, signal, effect } from '@angular/core';
import { Router, NavigationEnd, RouterOutlet } from '@angular/router';
import { Header } from './components/header/header';
import { Footer } from './components/footer/footer';
import { filter } from 'rxjs/operators';
import { CommonModule } from '@angular/common';
import { Sidebar } from './components/sidebar/sidebar';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, Header, Footer, CommonModule, Sidebar],
  templateUrl: './app.html',
  styleUrls: ['./app.css'],
  standalone: true
})

export class App {
  protected readonly title = signal('Breath of a New Kingdom');

  // rutas donde NO debe aparecer header/footer
  private rutasSinLayout = ['/login', '/register', '/auth-code', '/auth-error'];

  // signal para manejar si se muestra o no el layout
  mostrarLayout = signal(true);

  constructor(private router: Router) {
    // Detecta los cambios de ruta en tiempo real
    this.router.events.pipe(
      filter(event => event instanceof NavigationEnd)
    ).subscribe((event: any) => {
      const rutaActual = event.urlAfterRedirects;
      const ocultar = this.rutasSinLayout.some(r => rutaActual.startsWith(r));
      this.mostrarLayout.set(!ocultar);
    });
  }

  sidebarVisible = false;
  toggleSidebar() {
    this.sidebarVisible = !this.sidebarVisible;
  }
}
