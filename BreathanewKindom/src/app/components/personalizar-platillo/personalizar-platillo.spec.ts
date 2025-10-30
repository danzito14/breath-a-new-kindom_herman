import { ComponentFixture, TestBed } from '@angular/core/testing';

import { PersonalizarPlatillo } from './personalizar-platillo';

describe('PersonalizarPlatillo', () => {
  let component: PersonalizarPlatillo;
  let fixture: ComponentFixture<PersonalizarPlatillo>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [PersonalizarPlatillo]
    })
    .compileComponents();

    fixture = TestBed.createComponent(PersonalizarPlatillo);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
