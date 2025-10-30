import { Component, OnInit, Output, EventEmitter, NgZone, ChangeDetectorRef } from '@angular/core';
import { RouterModule } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-header',
  standalone: true,
  imports: [RouterModule, CommonModule],
  templateUrl: './header.html',
  styleUrls: ['./header.css']
})
export class Header implements OnInit {
  @Output() toggleSidebarEvent = new EventEmitter<void>();

  nicknameCorto: string = 'Mi perfil'; // valor inicial seguro
  usuario: any = null;

  constructor(
    private http: HttpClient,
    private zone: NgZone,
    private cd: ChangeDetectorRef // ⚡ inyectar ChangeDetectorRef
  ) { }

  ngOnInit(): void {
    this.getUsuario();
  }

  toggleSidebar() {
    this.toggleSidebarEvent.emit();
  }

  /** Obtiene el usuario usando el token JWT desde el backend */
  getUsuario() {
    if (typeof window === 'undefined') return; // evita error SSR
    const token = window.localStorage.getItem('token');
    if (!token) return;

    this.http.get('http://localhost:8000/user/get_user_id', {
      headers: { 'Authorization': `Bearer ${token}` }
    }).subscribe({
      next: (user: any) => {
        this.usuario = user;
        const nickname = user?.Nickname || 'Mi perfil';

        // ⚡ Asegura que Angular detecte el cambio
        this.zone.run(() => {
          this.nicknameCorto = this.truncarNickname(nickname);
          // fuerza detección de cambios
          this.cd.detectChanges();
        });
      },
      error: (err) => console.error('No se pudo obtener usuario', err)
    });
  }

  /** Trunca el nickname si supera los 10 caracteres */
  truncarNickname(nickname?: string): string {
    if (!nickname) return 'Mi perfil';
    return nickname.length > 10 ? nickname.slice(0, 10) + '..' : nickname;
  }
}
