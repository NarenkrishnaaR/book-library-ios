//
//  BookDetailView.swift
//  BookLibrary
//
//  Created by Naren on 27/03/25.
//

import SwiftUI

struct BookDetailView: View {
  let book: Book
  @State private var isExpanded = false
  
  var body: some View {
    Form {
      Text("Title - \(book.title)")
      Text("Author Name - \(book.authorName)")
      Text("Publication Year - \(book.publishedYear ?? "")")
      Text("Genre - \(book.genre)")
      Text("Category - \(book.category?.name ?? "")")
      Button(action: {
        isExpanded.toggle()
      }) {
        Text(isExpanded ? "Show Less" : "Show More")
          .frame(maxWidth: .infinity)
          .padding()
          .cornerRadius(8)
      }
      
      if isExpanded {
        Text("This is additional information about the book.")
          .foregroundColor(.gray)
      }
    }
    .animation(.default, value: isExpanded)
  }
}

