//
//  Category.swift
//  book-library-ios
//
//  Created by Naren on 26/03/25.
//

import Foundation
import SwiftData

@Model
final class Category {
  @Attribute(.unique) var name: String
  
  @Relationship(deleteRule: .cascade, minimumModelCount: 1, maximumModelCount: 10,
                inverse: \Book.category)
  var books: [Book] = []
  
  init(name: String, books: [Book]) {
    self.name = name
    self.books = books
  }
}

enum ReadingStatus: String, Codable, CaseIterable {
  case currentRead = "Cutly Reading"
  case toRead = "To Read"
  case completed = "Complted"
}
