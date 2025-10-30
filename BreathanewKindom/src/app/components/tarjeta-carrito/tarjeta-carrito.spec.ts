import { ComponentFixture, TestBed } from '@angular/core/testing';

import { TarjetaCarrito } from './tarjeta-carrito';

describe('TarjetaCarrito', () => {
  let component: TarjetaCarrito;
  let fixture: ComponentFixture<TarjetaCarrito>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [TarjetaCarrito]
    })
    .compileComponents();

    fixture = TestBed.createComponent(TarjetaCarrito);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
