import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Direccion } from './direccion';

describe('Direccion', () => {
  let component: Direccion;
  let fixture: ComponentFixture<Direccion>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Direccion]
    })
    .compileComponents();

    fixture = TestBed.createComponent(Direccion);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
