//
//  Book.swift
//  book-library-ios
//
//  Created by Naren on 26/03/25.
//

import Foundation
import SwiftData

@Model class Book {
  #Index([\Book.title])
  
  @Attribute(.unique) var title: String
  var authorName: String
  var publicationYear: Int32
  var publishedYear: String?
  var genre: BookGenre
  var isFavourite = false
  @Transient var isExpanded = false
  @Relationship var category: Category?
  
  init(title: String, authorName: String, publicationYear: Int32,
       genre: BookGenre, isFavourite: Bool,
       summary: String? = nil, category: Category? = nil,
       publishedYear: String) {
    self.title = title
    self.authorName = authorName
    self.publicationYear = publicationYear
    self.genre = genre
    self.isFavourite = isFavourite
    self.category = category
    self.publishedYear = publishedYear
  }
}

extension Book {
  enum BookGenre: String, Codable, CaseIterable {
    case fiction = "Fiction"
    case nonFiction = "Non-Fiction"
    case scienceFiction = "Science Fiction"
  }
  
}
