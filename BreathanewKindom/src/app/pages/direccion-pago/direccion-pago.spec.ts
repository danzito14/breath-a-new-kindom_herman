import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DireccionPago } from './direccion-pago';

describe('DireccionPago', () => {
  let component: DireccionPago;
  let fixture: ComponentFixture<DireccionPago>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DireccionPago]
    })
    .compileComponents();

    fixture = TestBed.createComponent(DireccionPago);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
