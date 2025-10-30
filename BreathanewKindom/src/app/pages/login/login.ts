import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { AuthService } from '../../services/auth/auth-service';
import { AuthStoreService } from '../../services/auth/auth-store';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './login.html',
  styleUrls: ['./login.css']
})
export class Login {
  usuario = '';
  contrasena = '';

  constructor(
    private authservice: AuthService,
    private authStore: AuthStoreService, // ✅ Inyecta aquí
    private router: Router
  ) { }

  onLogin(): void {
    this.authservice.login(this.usuario, this.contrasena).subscribe({
      next: (response) => {
        console.log('Login exitoso', response);

        // ✅ Guardar token en el AuthStoreService
        this.authStore.setToken(response.access_token);

        this.router.navigate(['']);
      },
      error: (error) => {
        console.error('Error al iniciar sesión', error);
        alert('Usuario o contraseña incorrectos');
      }
    });
  }
}
