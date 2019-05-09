import { Component, OnInit } from '@angular/core';
import { Person } from '../person.model'

@Component({
  selector: 'person-form',
  templateUrl: './person-form.component.html',
  styleUrls: ['./person-form.component.css']
})
export class PersonFormComponent implements OnInit {

  model = new Person(1, '', '', '@example.com', '', '+63');;
  constructor() { }

  ngOnInit() {
  }

  get currentPerson() { return JSON.stringify(this.model); }
}
