import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { RegisterService } from '../../services/auth/register';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [FormsModule, RouterModule],
  templateUrl: './register.html',
  styleUrls: ['./register.css']
})
export class Register {
  id_nvl_usuario = 1;
  Nickname = "";
  Contraseña = "";
  Nombre = "";
  Apellido = "";
  Correo_electronico = "";
  estatus = true;
  contrasena = "";
  contrasena2 = "";

  constructor(private registerservice: RegisterService, private router: Router) { }

  onRegister(): void {
    if (this.contrasena != this.contrasena2) {
      alert("No se ingreso la misma contraseña");
      return;
    }
    const nuevoUsuario = {
      id_nvl_usuario: this.id_nvl_usuario,
      Nickname: this.Nickname,
      contrasena: this.contrasena, // viene del HTML
      Nombre: this.Nombre,
      Apellido: this.Apellido,
      Correo_electronico: this.Correo_electronico,
      estatus: this.estatus
    };



    this.registerservice.registro(nuevoUsuario).subscribe({
      next: (response) => {
        console.log('Registro exitoso', response);
        this.router.navigate(['/auth-code']);
      },
      error: (error) => {
        console.error('Error al registrar', error);
        alert('Error al intentar registrar');
      }
    });
  }
}
